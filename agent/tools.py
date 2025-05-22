from kubernetes import client, config as k8s_config
from langchain.tools import tool
import datetime

# Reusable Kubernetes API clients
_core_v1_api = None
_apps_v1_api = None

def get_core_v1_api():
    global _core_v1_api
    if _core_v1_api is None:
        _core_v1_api = client.CoreV1Api()
    return _core_v1_api

def get_apps_v1_api():
    global _apps_v1_api
    if _apps_v1_api is None:
        _apps_v1_api = client.AppsV1Api()
    return _apps_v1_api

def load_kube_config(kubeconfig_path=None):
    try:
        if kubeconfig_path:
            k8s_config.load_kube_config(config_file=kubeconfig_path)
        else:
            k8s_config.load_incluster_config()
    except Exception as e:
        raise RuntimeError(f"Failed to load kube config: {e}")

@tool
def check_pod_status(namespace="default", pod_name=None):
    v1 = get_core_v1_api()
    try:
        if pod_name:
            pod = v1.read_namespaced_pod(pod_name, namespace)
            return [{"pod_name": pod.metadata.name, "status": pod.status.phase}]
        pods = v1.list_namespaced_pod(namespace)
        result = []
        for pod in pods.items:
            status = pod.status.phase
            if status != "Running":
                result.append({"pod_name": pod.metadata.name, "status": status})
        return result if result else [{"message": "All pods running"}]
    except Exception as e:
        raise RuntimeError(f"Error checking pod status: {e}")

@tool
def get_pod_logs(namespace, pod_name, container_name=None, tail_lines=100):
    v1 = get_core_v1_api()
    try:
        logs = v1.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            container=container_name,
            tail_lines=tail_lines
        )
        return logs
    except Exception as e:
        raise RuntimeError(f"Error getting pod logs: {e}")

@tool
def get_pod_events(namespace, pod_name, limit=10):
    v1 = get_core_v1_api()
    try:
        field_selector = f"involvedObject.name={pod_name}"
        events = v1.list_namespaced_event(namespace, field_selector=field_selector, limit=limit)
        return [{"message": event.message, "type": event.type, "timestamp": event.last_timestamp} for event in events.items]
    except Exception as e:
        raise RuntimeError(f"Error getting pod events: {e}")

@tool
def describe_pod(namespace, pod_name):
    v1 = get_core_v1_api()
    try:
        pod = v1.read_namespaced_pod(pod_name, namespace)
        return pod.to_dict()
    except Exception as e:
        raise RuntimeError(f"Error describing pod: {e}")

@tool
def get_node_status():
    v1 = get_core_v1_api()
    try:
        nodes = v1.list_node()
        result = []
        for node in nodes.items:
            name = node.metadata.name
            for cond in node.status.conditions:
                if cond.type == "Ready":
                    result.append({"node_name": name, "status": cond.status})
        return result
    except Exception as e:
        raise RuntimeError(f"Error getting node status: {e}")

@tool
def get_resource_usage(resource_type="pod", namespace="default", name=None):
    v1 = get_core_v1_api()
    try:
        # Placeholder for resource usage logic
        return {"message": "Resource usage functionality not implemented yet"}
    except Exception as e:
        raise RuntimeError(f"Error getting resource usage: {e}")

@tool
def check_deployment_status(namespace, deployment_name):
    apps_v1 = get_apps_v1_api()
    try:
        deployment = apps_v1.read_namespaced_deployment(deployment_name, namespace)
        return deployment.status.to_dict()
    except Exception as e:
        raise RuntimeError(f"Error checking deployment status: {e}")

@tool
def restart_deployment(namespace, deployment_name):
    apps_v1 = get_apps_v1_api()
    try:
        deployment = apps_v1.read_namespaced_deployment(deployment_name, namespace)
        # Patch deployment to trigger restart by updating an annotation with current timestamp
        patch = {
            "spec": {
                "template": {
                    "metadata": {
                        "annotations": {
                            "kubectl.kubernetes.io/restartedAt": datetime.datetime.utcnow().isoformat() + "Z"
                        }
                    }
                }
            }
        }
        apps_v1.patch_namespaced_deployment(deployment_name, namespace, patch)
        return {"message": f"Deployment {deployment_name} restarted"}
    except Exception as e:
        raise RuntimeError(f"Error restarting deployment: {e}")
