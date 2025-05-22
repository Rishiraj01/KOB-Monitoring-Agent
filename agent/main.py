import time
import logging
import threading
import asyncio
import uvicorn
from config import config
from tools import load_kube_config
from agent.agent import create_agent
from agent.alerter import Alerter

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("KOB_Monitor")

# Global state accessible by API
state = {
    "status": "Initializing",
    "last_alert_time": None,
    "anomalies_detected": 0,
    "last_error": None
}

def run_api_server():
    """Run FastAPI server in a separate thread"""
    if config.api_enabled:
        from api import app
        uvicorn.run(app, host="0.0.0.0", port=config.api_port)

async def check_node_status(agent, alerter):
    logger.debug("Checking node status")
    node_status = agent.tools["get_node_status"].run()
    # node_status is now structured data (list of dicts)
    not_ready_nodes = [n for n in node_status if n.get("status") != "True"]
    if not_ready_nodes:
        logger.warning(f"Detected NotReady nodes: {not_ready_nodes}")
        diagnosis = agent.run(f"Diagnose why nodes are not ready: {not_ready_nodes}")
        alert = {
            "anomaly_type": "NotReadyNode",
            "anomaly": not_ready_nodes,
            "diagnosis": diagnosis,
            "timestamp": time.time()
        }
        alerter.send_alert(alert)
        state["last_alert_time"] = time.time()
        state["anomalies_detected"] += 1

async def check_pods_in_namespace(agent, alerter, namespace):
    state["status"] = f"Checking namespace: {namespace}"
    logger.debug(f"Checking pods in namespace: {namespace}")
    pod_status = agent.tools["check_pod_status"].run(namespace=namespace)
    problem_indicators = ["Pending", "CrashLoopBackOff", "Error", "ImagePullBackOff", "Failed"]
    problematic_pods = [p for p in pod_status if any(indicator in p.get("status", "") for indicator in problem_indicators)]
    if problematic_pods:
        logger.warning(f"Pod issues detected in namespace {namespace}: {problematic_pods}")
        diagnosis = agent.run(f"Diagnose pod issues in namespace {namespace}: {problematic_pods}")
        alert = {
            "anomaly_type": "PodIssue",
            "anomaly": problematic_pods,
            "diagnosis": diagnosis,
            "namespace": namespace,
            "timestamp": time.time()
        }
        alerter.send_alert(alert)
        state["last_alert_time"] = time.time()
        state["anomalies_detected"] += 1
        if config.enable_auto_fix:
            logger.info("Auto-fix enabled, checking if deployment restart is necessary")
            # Auto-fix logic would go here based on config.auto_fix_rules

async def monitor_loop():
    """Main monitoring loop with async concurrency"""
    try:
        logger.info("Loading Kubernetes configuration")
        load_kube_config(config.kubeconfig)
        
        logger.info(f"Initializing agent with LLM provider: {config.llm_provider}")
        agent = create_agent(config)
        
        logger.info(f"Connecting to RabbitMQ at {config.rabbitmq_host}:{config.rabbitmq_port}")
        alerter = Alerter(config.rabbitmq_host, config.rabbitmq_port, config.rabbitmq_queue)

        state["status"] = "Monitoring"
        logger.info(f"Monitoring started. Checking namespaces: {config.monitored_namespaces}")

        while True:
            try:
                await check_node_status(agent, alerter)
                tasks = [check_pods_in_namespace(agent, alerter, ns) for ns in config.monitored_namespaces]
                await asyncio.gather(*tasks)
                state["status"] = "Monitoring"
                await asyncio.sleep(config.polling_interval)
            except Exception as e:
                logger.error(f"Error during monitoring: {e}", exc_info=True)
                state["last_error"] = str(e)
                await asyncio.sleep(10)  # Shorter sleep on error
                
    except Exception as e:
        logger.critical(f"Critical error in monitor loop: {e}", exc_info=True)
        state["status"] = "Error"
        state["last_error"] = str(e)

def main():
    """Main entry point"""
    # Start API server in separate thread if enabled
    if config.api_enabled:
        api_thread = threading.Thread(target=run_api_server, daemon=True)
        api_thread.start()
        logger.info(f"API server started on port {config.api_port}")
    
    # Start monitoring
    try:
        asyncio.run(monitor_loop())
    except KeyboardInterrupt:
        logger.info("Received shutdown signal, exiting...")
    except Exception as e:
        logger.critical(f"Critical error: {e}", exc_info=True)
        return 1
    return 0

if __name__ == "__main__":
    exit(main())
