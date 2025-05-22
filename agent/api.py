from fastapi import FastAPI
import time
from config import config
from main import state

app = FastAPI(title="KOB Monitoring Agent API", 
             description="API for the AI-powered Kubernetes on Bare Metal monitoring agent")

@app.get("/status")
def get_status():
    """Get the current status of the monitoring agent"""
    return {
        "status": state["status"],
        "last_alert_time": state["last_alert_time"],
        "anomalies_detected": state["anomalies_detected"],
        "last_error": state["last_error"],
        "uptime": time.time() - state.get("start_time", time.time()),
        "config": {
            "monitored_namespaces": config.monitored_namespaces,
            "llm_provider": config.llm_provider,
            "polling_interval": config.polling_interval,
            "enable_auto_fix": config.enable_auto_fix
        }
    }

@app.get("/health")
def health_check():
    """Simple health check endpoint"""
    return {"status": "ok"}
