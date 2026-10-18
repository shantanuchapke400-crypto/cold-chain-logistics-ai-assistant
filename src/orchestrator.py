import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver 


# 1. Setup and Resolution
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parents[0]

if str (project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.agent_tools import query_telemetry_db, fetch_corridor_conditions, search_compliance_sop

load_dotenv(project_root / ".env")

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


# 2. FACTORY INITIALIZATION: AGENT REASONER LLM

AGENT_LLM_SETTING = (
    os.getenv("Agent_llm", "GROQ").strip().upper()
)

if AGENT_LLM_SETTING == "GROQ":
    print("🤖 Brain Mode: Utilizing Groq Cloud Reasoner...")

    from langchain_groq import ChatGroq

    llm = ChatGroq(
        model="openai/gpt-oss-20b",
        temperature=0,
        max_tokens=1024,
    )

elif AGENT_LLM_SETTING == "OLLAMA":
    print(
        "🤗 Brain Mode: Local Fallback Activated. "
        "Binding Local Ollama (qwen2.5:7b)..."
    )

    from langchain_ollama import ChatOllama

    llm = ChatOllama(
        model="qwen2.5:7b",
        temperature=0,
        num_predict=1024,
    )

else:
    raise ValueError(
        f"Unsupported LLM provider: {AGENT_LLM_SETTING}. "
        "Choose GROQ or OLLAMA."
    )

fde_tools = [
    query_telemetry_db,
    fetch_corridor_conditions,
    search_compliance_sop,
]

llm_with_tools = llm.bind_tools(fde_tools)

# 3. Graph Architecture Assembly 
def reasoning_node(state: AgentState):
    response = llm_with_tools.invoke(state["messages"])
    return{"messages": [response]}

print("⚙️ Compiling LangGraph FDE Orchestrator...")
graph_builder = (StateGraph(AgentState))
graph_builder.add_node("reasoner", reasoning_node)
graph_builder.add_node("tools", ToolNode(fde_tools))

graph_builder.add_edge(START, "reasoner")
graph_builder.add_conditional_edges("reasoner", tools_condition)
graph_builder.add_edge("tools", "reasoner")

fde_agent = graph_builder.compile(checkpointer=MemorySaver())


# Chat loop testing panel

if __name__ == "__main__":
    print("\n" + "=" * 55)
    print("🚀 FDE Supply Chain Orchestrator Online")
    print(
        f"   Configured Execution: "
        f"[LLM: {AGENT_LLM_SETTING}] -> "
        f"[Embeddings: {os.getenv('Embeddings_model', 'LOCAL')}]"
    )
    print("=" * 55 + "\n")

    # Load system prompt
    prompt_path = project_root / "src" / "prompts" / "system_prompt.txt"

    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_instructions = f.read()
    except FileNotFoundError:
        print(f"Warning: Prompt file not found: {prompt_path}")
        system_instructions = "You are a helpful cold-chain logistics assistant."

    system_prompt = SystemMessage(content=system_instructions)
    thread_config = {
        "configurable": {"thread_id": "production_test_1"}
    }

    # Initialize conversation state
    fde_agent.invoke(
        {"messages": [system_prompt]},
        config=thread_config,
    )

    while True:
        try:
            user_input = input("\nDispatcher > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting FDE Agent.")
            break

        if user_input.lower() in {"exit", "quit"}:
            print("Exiting FDE Agent.")
            break

        if not user_input:
            continue

        try:
            events = fde_agent.stream(
                {"messages": [("user", user_input)]},
                config=thread_config,
                stream_mode="updates",
            )

            for event in events:
                for node_name, node_state in event.items():
                    if node_name == "tools":
                        print(
                            "   [System] Retrieving external data via tools..."
                        )

                    elif node_name == "reasoner":
                        latest_msg = node_state["messages"][-1]

                        if latest_msg.content:
                            print(f"\n🤖 FDE Agent:\n{latest_msg.content}")

        except Exception as e:
            print(f"\nAgent error: {type(e).__name__}: {e}")
