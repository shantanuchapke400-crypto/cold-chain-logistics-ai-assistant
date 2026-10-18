# 🚚 Cold Chain Logistics AI Assistant

An AI-powered logistics assistant designed to help analyze cold-chain fleet conditions, retrieve incident-handling procedures, and support operational decision-making using LLMs, retrieval-augmented generation (RAG), and structured telemetry data.

## 📌 Overview

Cold-chain logistics requires careful monitoring of temperature-sensitive cargo, fleet conditions, route risks, and operational incidents. This project combines data access, semantic document retrieval, and AI agent orchestration into a single assistant.

The goal is to make logistics information easier to query through natural language while keeping database access controlled and responses grounded in available operational data.

## ✨ Key Features

- **AI Agent Orchestration:** Uses LangGraph to coordinate reasoning and tool execution.
- **Natural-Language Interaction:** Ask questions about fleet conditions and incident procedures.
- **SQL Server Integration:** Accesses fleet telemetry through a structured database view.
- **RAG-Based SOP Retrieval:** Uses embeddings and Pinecone for semantic search over cold-chain incident procedures.
- **Local Embeddings:** Supports the `BAAI/bge-m3` embedding model.
- **Local LLM Support:** Integrates Ollama with the `qwen2.5:7b` model.
- **Read-Only Database Access:** Uses a restricted SQL login for operational queries.
- **Streamlit Interface:** Provides a user-facing application interface.

## 🏗️ Technology Stack

| Component | Technology |
|---|---|
| Language | Python |
| Agent orchestration | LangGraph |
| LLM integration | LangChain, Ollama |
| Local language model | Qwen 2.5 7B |
| Embeddings | Hugging Face, BAAI/bge-m3 |
| Vector database | Pinecone |
| Operational database | Microsoft SQL Server |
| User interface | Streamlit |
| Containerization | Docker |
| Configuration | Python dotenv |
| Version control | Git and GitHub |

## 🧠 Architecture

```text
                 User Query
                     |
                     v
              Streamlit UI
                 src/ui.py
                     |
                     v
          LangGraph Orchestrator
             src/orchestrator.py
                     |
          +----------+----------+
          |          |          |
          v          v          v
      Telemetry    Corridor    SOP Search
       SQL Tool    Tool        Pinecone
          |          |          |
          v          v          v
       SQL Server  Conditions  Retrieved
                   Provider    Documents
          |          |          |
          +----------+----------+
                     |
                     v
             LLM Reasoning
                     |
                     v
               Final Answer
```

*Note: The architecture illustrates the intended tool-based workflow. Actual results depend on tool availability, retrieved context, and the quality of the underlying data.*

## 📂 Project Structure

```text
cold-chain-logistics-ai-assistant/
├── Materials/
│   ├── FDE-YT-Project-Business-Presentation.pdf
│   └── Technical Design Document (TDD)_ Cold-Chain Logistics AI-Assistant.pdf
├── data/
│   ├── policy/
│   │   └── Cold_Chain_Incident_SOP_v2.md
│   └── source/
│       └── data.txt
├── docs/
│   └── instructions.md
├── scripts/
│   ├── ingest_legecy_data.py
│   ├── ingest_sop_pipcone.py
│   └── setup_security_and_view.sql
├── src/
│   ├── prompts/
│   │   └── system_prompt.txt
│   ├── agent_tools.py
│   ├── orchestrator.py
│   └── ui.py
├── .gitignore
├── requirements.txt
└── test_db_connection.py
```

## ⚙️ Prerequisites

Before running the project, install or configure:

- Python and a virtual environment
- Docker Desktop
- Microsoft SQL Server container
- Pinecone account and API key
- Ollama and the Qwen 2.5 7B model
- Hugging Face model access
- Git

Some components require external services or local resources. Hardware requirements depend on the selected language and embedding models.

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/shantanuchapke400-crypto/cold-chain-logistics-ai-assistant.git
cd cold-chain-logistics-ai-assistant
```

### 2. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

If a dependency is missing, install the compatible package version required by the project.

### 4. Configure environment variables

Create a local `.env` file in the project root. Configure the required SQL Server, Pinecone, embedding, and LLM settings according to the project's code and `docs/instructions.md`.

Keep API keys and database credentials private. Never commit `.env` to GitHub.

### 5. Start the supporting services

Start your SQL Server container and verify the database connection. Configure Ollama and download the required model if you plan to use local inference.

The SQL database must contain the expected fleet telemetry table and semantic view before the telemetry tools can work.

### 6. Prepare the vector index

Use the SOP ingestion script to process the incident procedure document, generate embeddings, and populate the configured Pinecone index.

```powershell
python scripts/ingest_sop_pipcone.py
```

Verify that the Pinecone index name and embedding dimension match the configuration.

### 7. Run the application

Launch the Streamlit interface:

```powershell
python -m streamlit run src/ui.py
```

Alternatively, run the agent orchestrator directly if you want to test the agent workflow independently.

## 🔐 Security

Security is an important part of this project.

- Keep credentials in environment variables.
- Use a restricted SQL login for agent queries.
- Grant access only to the database views required by the application.
- Avoid exposing SQL Server or Ollama ports publicly.
- Do not commit datasets, generated caches, credentials, or local environment files.
- Validate AI-generated answers against actual tool outputs before using them for operational decisions.

## 🛠️ Current Development Status

The project includes the core application structure, SQL Server telemetry ingestion, a restricted database access pattern, LangGraph orchestration, local model integration, and SOP retrieval components.

Cloud deployment and end-to-end validation of the complete workflow remain areas to verify before treating the application as production-ready.

## 🔮 Future Improvements

- Improve response grounding and tool-output validation.
- Add automated tests for database queries, retrieval, and agent workflows.
- Evaluate retrieval quality and response accuracy.
- Add monitoring, structured logging, and error handling.
- Improve deployment configuration and external service management.
- Explore containerized deployment and cloud infrastructure.

## 👨‍💻 Author

**Shantanu Chapke**

BCA Student | Aspiring AI/ML Engineer

- GitHub: [@shantanuchapke400-crypto](https://github.com/shantanuchapke400-crypto)
- Project Repository: [Cold Chain Logistics AI Assistant](https://github.com/shantanuchapke400-crypto/cold-chain-logistics-ai-assistant)

## 📄 License

No license has been specified yet. Add a `LICENSE` file if you intend to define how others may use, modify, and distribute this project.
