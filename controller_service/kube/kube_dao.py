import subprocess
import time
from collections import defaultdict

from kubernetes import client, config
from kubernetes.client.rest import ApiException

MONSTER_NAMES = {
    "alienoid",
    "boogie-woogie",
    "giga-zaur",
    "the-king",
    "kraken",
    "meka-dragon",
    "pandakai",
    "pumpkin-jack",
    "space-penguin",
}


class KubeDao:
    def __init__(self):
        subprocess.run(["minikube", "start"], check=True)
        config.load_kube_config()
        self.client = client.CoreV1Api()

    def list_all_namespaces(self):
        namespace_list = self.client.list_namespace()
        namespaces = []
        for ns in namespace_list.items:
            namespace = {"name": ns.metadata.name}
            if ns.metadata.labels and "location" in ns.metadata.labels:
                namespace["location"] = ns.metadata.labels["location"]
                namespaces.append(namespace)

        print(f"All listed namespaces:\n{namespaces}")
        return namespaces

    def create_namespaces(self, location_names):
        for name in location_names:
            namespace = client.V1Namespace(
                metadata=client.V1ObjectMeta(name=name, labels={"location": name})
            )
            self.client.create_namespace(body=namespace)

    def delete_namespace(self, namespace):
        self.client.delete_namespace(name=namespace)

    def delete_all_namespaces(self):
        namespaces = self.list_all_namespaces()
        for ns in namespaces:
            self.client.delete_namespace(ns["name"])

    def list_all_pods(self):
        pods = self.client.list_pod_for_all_namespaces().items
        pods_by_namespaces = defaultdict(list)
        for pod in pods:
            namespace = pod.metadata.namespace
            if namespace and pod.metadata.name in MONSTER_NAMES:
                pods_by_namespaces[namespace].append(pod.metadata.name)

        return pods_by_namespaces

    def create_pod(
        self,
        pod_name,
        namespace,
        image="nginx",
        container_port=80,
    ):
        print(f"Creating pod '{pod_name}' in '{namespace}")
        pod_manifest = client.V1Pod(
            metadata=client.V1ObjectMeta(
                name=pod_name, labels={"monster-name": pod_name}
            ),
            spec=client.V1PodSpec(
                containers=[
                    client.V1Container(
                        name=pod_name,
                        image=image,
                        ports=[client.V1ContainerPort(container_port=container_port)],
                    )
                ],
                node_name="minikube",
            ),
        )

        self.client.create_namespaced_pod(namespace=namespace, body=pod_manifest)
        return self.expose_pod_port(pod_name, namespace)

    def expose_pod_port(self, pod_name, namespace):
        service_name = f"{pod_name}-state-service"
        service_spec = client.V1Service(
            metadata=client.V1ObjectMeta(name=service_name),
            spec=client.V1ServiceSpec(
                selector={"monster-name": pod_name},
                type="NodePort",
                ports=[client.V1ServicePort(port=80, target_port=80)],
            ),
        )

        service = self.client.create_namespaced_service(
            namespace=namespace, body=service_spec
        )
        return service.spec.ports[0].node_port

    def delete_pod(self, pod_name, namespace):
        print(f"Deleting pod '{pod_name}' in namespace '{namespace}")
        self.client.delete_namespaced_pod(name=pod_name, namespace=namespace)

    def get_pod(self, pod_name, namespace):
        pod = self.client.read_namespaced_pod(name=pod_name, namespace=namespace)
        return pod

    def move_pod(self, pod_name, from_namespace, target_namespace):
        pod = self.get_pod(pod_name, from_namespace)
        self.delete_pod(pod_name, from_namespace)
        self.wait_for_pod_deletion(pod_name, from_namespace)

        containers = []
        for c in pod.spec.containers:
            clean_c = client.V1Container(
                name=c.name,
                image=c.image,
                ports=c.ports,
                env=c.env,
                command=c.command,
                args=c.args,
                resources=c.resources,
                volume_mounts=[
                    vm
                    for vm in (c.volume_mounts or [])
                    if not vm.name.startswith("kube-api-access")
                ],
            )
            containers.append(clean_c)

        pod_manifest = client.V1Pod(
            metadata=client.V1ObjectMeta(name=pod_name, labels=pod.metadata.labels),
            spec=client.V1PodSpec(
                containers=containers,
                volumes=[
                    v
                    for v in (pod.spec.volumes or [])
                    if not v.name.startswith("kube-api-access")
                ],
            ),
        )

        print(f"Recreating pod '{pod_name}'")
        self.client.create_namespaced_pod(namespace=target_namespace, body=pod_manifest)
        self.wait_for_pod_ready(pod_name, target_namespace)

    def get_ip(self):
        return subprocess.check_output(["minikube", "ip"], text=True).strip()

    def wait_for_pod_deletion(self, pod_name, namespace, timeout=60):
        print(f"Waiting for pod deletion of '{pod_name}'")
        for _ in range(timeout):
            try:
                self.client.read_namespaced_pod(pod_name, namespace)
            except ApiException as e:
                if e.status == 404:
                    return
                else:
                    raise
            time.sleep(1)
        raise TimeoutError(f"Pod {pod_name} deletion timed out after {timeout} seconds")

    def wait_for_pod_ready(self, pod_name, namespace, timeout=120):
        print(f"Waiting for pod startup of '{pod_name}'")
        for _ in range(timeout):
            pod = self.client.read_namespaced_pod(pod_name, namespace)
            if pod.status.phase == "Running":
                conditions = pod.status.conditions or []
                ready = any(
                    c.type == "Ready" and c.status == "True" for c in conditions
                )
                if ready:
                    return

            time.sleep(2)

        raise TimeoutError(f"Pod {pod_name} start up timed out after {timeout} seconds")
