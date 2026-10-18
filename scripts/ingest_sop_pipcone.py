import os
import hashlib
import json
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd
import pypdf


from pinecone import Pinecone, ServerlessSpec
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeEmbeddings
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_pinecone import PineconeVectorStore


os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"]= "true"

# Path resoulution and setup
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
load_dotenv(project_root / ".env")

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

if not PINECONE_API_KEY:
    raise ValueError("Missing PINECONE_API_KEY in.env")

# Clean production data
cache_dir = project_root / "data" / "cache"
cache_dir.mkdir(parents=True, exist_ok=True)
HASH_CACHE_FILE = cache_dir / "ingestion_hash_cache.json"

hash_cache = {}
if HASH_CACHE_FILE.exists():
    try:
        with open(HASH_CACHE_FILE,"r") as f:
            hash_cache = json.load(f)
    except Exception:
        hash_cache = {}


# 2. DYNAMIC EMBEDDING MODEL CONFIGURATION

import os
from langchain_huggingface import HuggingFaceEmbeddings

EMBEDDINGS_MODEL_SETTING = (
    os.getenv("Embeddings_model", "LOCAL").strip().upper()
)

if EMBEDDINGS_MODEL_SETTING != "LOCAL":
    raise ValueError(
        f"Unsupported embedding setting: {EMBEDDINGS_MODEL_SETTING}. "
        "This configuration supports LOCAL embeddings only."
    )

local_model_target = os.getenv(
    "Local_Embedding_Model",
    "BAAI/bge-m3"
).strip()

print(f"Loading local embedding model: {local_model_target}")

embeddings = HuggingFaceEmbeddings(
    model_name=local_model_target,
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)

INDEX_NAME = "fde-sop-index-local"
TARGET_DIMENSION = 1024

# Verify the actual output dimension
test_embedding = embeddings.embed_query(
    "Cold-chain logistics temperature incident"
)

actual_dimension = len(test_embedding)

if actual_dimension != TARGET_DIMENSION:
    raise ValueError(
        f"Embedding dimension mismatch: expected {TARGET_DIMENSION}, "
        f"got {actual_dimension}. Check your Pinecone index configuration."
    )

print(f"Embedding model loaded successfully: {local_model_target}")
print(f"Embedding dimension: {actual_dimension}")
print(f"Pinecone index target: {INDEX_NAME}")


# 3. PINECONE PROVISIONING
print(f"Connecting to Pinecone Index Target: [{INDEX_NAME}]...")
pc = Pinecone(api_key=PINECONE_API_KEY)

existing_indexes = pc.list_indexes().names()

# Self-healing verification in case an index was created with a wrong legacy dimension
if INDEX_NAME in existing_indexes:
    desc = pc.describe_index(INDEX_NAME)
    if desc.dimension != TARGET_DIMENSION:
        print(f"⚠️ Fixing tracking: Purging mismatched {desc.dimension} dim index...")
        pc.delete_index(INDEX_NAME)
        existing_indexes = [name for name in existing_indexes if name != INDEX_NAME]

if INDEX_NAME not in existing_indexes:
    print(f"Creating isolated target index: {INDEX_NAME} ({TARGET_DIMENSION} Dim)...")
    pc.create_index(
        name=INDEX_NAME,
        dimension=TARGET_DIMENSION, 
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )

index_client = pc.Index(INDEX_NAME)
vector_store = PineconeVectorStore(index_name=INDEX_NAME, embedding=embeddings)

# 4. ROBUST POLYMORPHIC PARSER
def parse_and_chunk_document(doc_path: Path) -> list[Document]:
    ext = doc_path.suffix.lower()
    raw_chunks: list[Document] = []

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=60,
    )

    try:
        if ext == ".md":
            headers_to_split_on = [
                ("#", "Header_1"),
                ("##", "Header_2"),
                ("###", "Header_3"),
            ]

            raw_text = doc_path.read_text(encoding="utf-8")

            if not raw_text.strip():
                return []

            md_splitter = MarkdownHeaderTextSplitter(
                headers_to_split_on=headers_to_split_on
            )
            header_docs = md_splitter.split_text(raw_text)

            # Preserve source path and header metadata
            for doc in header_docs:
                doc.metadata["source"] = str(doc_path)

            raw_chunks = text_splitter.split_documents(header_docs)

        elif ext == ".txt":
            raw_text = doc_path.read_text(encoding="utf-8")

            if not raw_text.strip():
                return []

            raw_docs = [
                Document(
                    page_content=raw_text,
                    metadata={"source": str(doc_path)},
                )
            ]
            raw_chunks = text_splitter.split_documents(raw_docs)

        elif ext == ".pdf":
            pdf_docs = []

            with open(doc_path, "rb") as file:
                reader = pypdf.PdfReader(file)

                for page_num, page in enumerate(reader.pages, start=1):
                    page_text = page.extract_text()

                    if page_text and page_text.strip():
                        pdf_docs.append(
                            Document(
                                page_content=page_text,
                                metadata={
                                    "source": str(doc_path),
                                    "page_number": page_num,
                                },
                            )
                        )

            raw_chunks = text_splitter.split_documents(pdf_docs)

        elif ext in [".csv", ".xlsx"]:
            df = (
                pd.read_csv(doc_path)
                if ext == ".csv"
                else pd.read_excel(doc_path)
            )

            for idx, row in df.iterrows():
                row_items = [
                    f"{col}: {val}"
                    for col, val in row.items()
                    if pd.notna(val) and str(val).strip()
                ]

                if row_items:
                    row_text = " | ".join(row_items)

                    raw_chunks.append(
                        Document(
                            page_content=row_text,
                            metadata={
                                "source": str(doc_path),
                                "row_index": int(idx),
                            },
                        )
                    )

        else:
            print(f"  ⚠️ Unsupported file type: {ext}")
            return []

    except Exception as e:
        print(f"  ❌ Error parsing {doc_path.name}: {e}")
        return []

# Clean and validate chunks
    valid_chunks = []

    for chunk in raw_chunks:
        chunk.page_content = chunk.page_content.strip()

        if chunk.page_content:
            valid_chunks.append(chunk)

    return valid_chunks

# 5. INCREMENTAL PIPELINE WITH BATCHING
policy_dir = project_root / "data" / "policy"
target_patterns = ["*.md", "*.txt", "*.pdf", "*.csv", "*.xlsx"]
current_files = {}
for pattern in target_patterns:
    for file_path in policy_dir.glob(pattern):
        current_files[file_path.name] = file_path

print(f"Found {len(current_files)} policy file(s) in {policy_dir}...")

updated_cache = {}
cache_modified = False

cached_filenames = set(hash_cache.keys())
current_filenames = set(current_files.keys())
deleted_files = cached_filenames - current_filenames

for deleted_file in deleted_files:
    print(f"🗑️ Detected deleted file: {deleted_file}. Purging from Pinecone...")
    try:
        index_client.delete(filter={"source_file": {"$eq": deleted_file}})
        cache_modified = True
    except Exception as e:
        print(f"  ❌ Failed to purge {deleted_file}: {e}")

for file_name, file_path in current_files.items():
    file_bytes = file_path.read_bytes()
    file_hash = hashlib.md5(file_bytes).hexdigest()
    updated_cache[file_name] = file_hash
    
    if hash_cache.get(file_name) == file_hash:
        print(f"✨ Skipped (Unchanged): {file_name}")
        continue
        
    print(f"🔄 Processing updates: {file_name}...")
    cache_modified = True
    
    try:
        try:
            index_client.delete(filter={"source_file": {"$eq": file_name}})
        except Exception:
            pass 
        
        chunks = parse_and_chunk_document(file_path)
        if not chunks:
            print(f"  ⚠️ No valid text chunks extracted from {file_name}.")
            continue
            
        explicit_ids = []
        for idx, chunk in enumerate(chunks):
            chunk.metadata["source_file"] = file_name
            chunk.metadata["file_format"] = file_path.suffix.replace(".", "").upper()
            chunk.metadata["document_type"] = "Compliance Asset"
            explicit_ids.append(f"{file_name}-chunk-{idx}")
            
        batch_size = 100
        total_chunks = len(chunks)
        print(f"  📤 Upserting {total_chunks} chunk(s) in batches of {batch_size}...")
        
        for i in range(0, total_chunks, batch_size):
            batch_docs = chunks[i : i + batch_size]
            batch_ids = explicit_ids[i : i + batch_size]
            vector_store.add_documents(documents=batch_docs, ids=batch_ids)
            
    except Exception as e:
        print(f"❌ Error during ingestion of {file_name}: {e}")
        updated_cache.pop(file_name, None)

# 6. SYNC HASH CACHE
if cache_modified:
    with open(HASH_CACHE_FILE, "w") as f:
        json.dump(updated_cache, f, indent=4)
    print("✅ Ingestion & cache update complete.")
else:
    print("🌴 Index is already up-to-date.")


