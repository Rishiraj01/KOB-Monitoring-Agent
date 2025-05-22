from langchain.agents import initialize_agent, AgentType
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.tools import Tool
from rag_setup import setup_rag_index, get_rag_retriever
import tools
import logging

# Add Gemini support
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logging.warning("Google Generative AI package not found. Gemini will not be available.")

def create_agent(config):
    # Choose LLM based on provider
    if config.llm_provider == "openai":
        llm = ChatOpenAI(
            model=config.llm_model,
            api_key=config.llm_api_key, 
            base_url=config.llm_endpoint or None,
            temperature=0.1
        )
    elif config.llm_provider == "gemini" and GEMINI_AVAILABLE:
        llm = ChatGoogleGenerativeAI(
            model=config.llm_model,
            google_api_key=config.llm_api_key,
            temperature=0.1
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {config.llm_provider}")
    
    rag_index = setup_rag_index(config.rag_docs_path)
    rag_retriever = get_rag_retriever(rag_index)

    rag_tool = Tool(
        name="KubernetesRAG",
        func=lambda query: "\n".join([doc.text for doc in rag_retriever.retrieve(query)]),
        description="Retrieves relevant Kubernetes documentation for troubleshooting."
    )

    agent = initialize_agent(
        tools=[
            tools.check_pod_status,
            tools.get_pod_logs,
            tools.get_pod_events,
            tools.describe_pod,
            tools.get_node_status,
            tools.get_resource_usage,
            tools.check_deployment_status,
            tools.restart_deployment,
            rag_tool
        ],
        llm=llm,
        agent=AgentType.OPENAI_FUNCTIONS if config.llm_provider == "openai" else AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True
    )
    return agent
