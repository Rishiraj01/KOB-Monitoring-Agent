import os
import json

class Config:
    def __init__(self):
        self.kubeconfig = os.getenv("KUBECONFIG")
        self.monitored_namespaces = os.getenv("MONITORED_NAMESPACES", "default").split(",")
        self.llm_provider = os.getenv("LLM_PROVIDER", "openai").lower()  # 'openai' or 'gemini'
        self.llm_api_key = os.getenv("LLM_API_KEY")
        self.llm_endpoint = os.getenv("LLM_ENDPOINT")  # For OpenAI, can be custom endpoint
        self.llm_model = os.getenv("LLM_MODEL", "gpt-4" if self.llm_provider == "openai" else "gemini-pro")
        self.rabbitmq_host = os.getenv("RABBITMQ_HOST", "localhost")
        self.rabbitmq_port = int(os.getenv("RABBITMQ_PORT", "5672"))
        self.rabbitmq_queue = os.getenv("RABBITMQ_QUEUE", "k8s-monitor-alerts")
        self.polling_interval = int(os.getenv("POLLING_INTERVAL_SECONDS", "60"))
        self.rag_docs_path = os.getenv("RAG_DOCS_PATH", "./docs")
        self.enable_auto_fix = os.getenv("ENABLE_AUTO_FIX", "false").lower() == "true"
        self.auto_fix_rules = json.loads(os.getenv("AUTO_FIX_RULES", "{}"))
        self.api_enabled = os.getenv("API_ENABLED", "false").lower() == "true"
        self.api_port = int(os.getenv("API_PORT", "8080"))

    def validate(self):
        assert self.llm_api_key, "LLM_API_KEY is required"
        assert self.llm_provider in ["openai", "gemini"], "LLM_PROVIDER must be 'openai' or 'gemini'"
        assert self.rag_docs_path, "RAG_DOCS_PATH is required"
        # Add more validations as needed

config = Config()
config.validate()
