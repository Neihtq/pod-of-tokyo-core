import os
import subprocess
import threading
import time
from collections import defaultdict

from dotenv import load_dotenv
from kubernetes import client, config
from kubernetes.client.rest import ApiException

from pod_of_tokyo_commons.constants import MONSTER_NAMES_SET, OUTSIDE_KEY

load_dotenv()

STATE_SERVICE_DOCKER_IMAGE = "neiht/state-service:latest"
DB_HOST = "postgres-service.default.svc.cluster.local"
DB_PORT = "5432"

POSTGRES_YAML_PATH = "database_service/postgres.yaml"


class KubeDao:
    def __init__(self):
        subprocess.run(["minikube", "start"], check=True)
        config.load_kube_config()
        self.v1 = client.CoreV1Api()

        subprocess.run(["kubectl", "apply", "-f", POSTGRES_YAML_PATH])

        thread = threading.Thread(target=self._start_minikube_tunnel, daemon=True)
        thread.start()

        time.sleep(1)

    def _start_minikube_tunnel(self):
        subprocess.run(["minikube", "tunnel"], check=True)

    def list_all_namespaces(self):
        namespace_list = self.v1.list_namespace(label_selector="location")
        namespaces = []
        for ns in namespace_list.items:
            namespaces.append(ns.metadata.name)

        print(f"All listed namespaces:\n{namespaces}")
        return namespaces

    def create_namespaces(self, location_names):
        for name in location_names:
            namespace = client.V1Namespace(
                metadata=client.V1ObjectMeta(name=name, labels={"location": name})
            )
            self.v1.create_namespace(body=namespace)

    def delete_namespace(self, namespace):
        self.v1.delete_namespace(name=namespace)

    def delete_all_namespaces(self):
        namespaces = self.list_all_namespaces()
        for ns in namespaces:
            self.v1.delete_namespace(ns)

    def list_all_pods(self):
        pods = self.v1.list_pod_for_all_namespaces().items
        pods_by_namespaces = defaultdict(list)
        for pod in pods:
            namespace = pod.metadata.namespace
            if namespace and pod.metadata.name in MONSTER_NAMES_SET:
                pods_by_namespaces[namespace].append(pod.metadata.name)

        return pods_by_namespaces

    def get_postgres_pods(self):
        pods = self.v1.list_namespaced_pod(
            namespace="default", label_selector="app=postgres"
        )
        pods_by_namespaces = defaultdict(list)
        for pod in pods.items:
            namespace = pod.metadata.namespace
            pods_by_namespaces[namespace].append(pod.metadata.name)

        return pods_by_namespaces

    def create_pod(
        self,
        pod_name,
        namespace,
        player_id,
        service_port,
        image=STATE_SERVICE_DOCKER_IMAGE,
    ):
        print(f"Creating pod '{pod_name}' in '{namespace}'")
        pod_manifest = client.V1Pod(
            metadata=client.V1ObjectMeta(
                name=pod_name, labels={"monster-name": pod_name}
            ),
            spec=client.V1PodSpec(
                containers=[
                    client.V1Container(
                        name=pod_name,
                        image=image,
                        ports=[client.V1ContainerPort(container_port=service_port)],
                        env=[
                            client.V1EnvVar(
                                name="DB_NAME", value=os.environ["DB_NAME"]
                            ),
                            client.V1EnvVar(
                                name="DB_USER", value=os.environ["DB_USER"]
                            ),
                            client.V1EnvVar(
                                name="DB_PASSWORD", value=os.environ["DB_PASSWORD"]
                            ),
                            client.V1EnvVar(name="DB_HOST", value=DB_HOST),
                            client.V1EnvVar(name="DB_PORT", value=DB_PORT),
                            client.V1EnvVar(name="PLAYER_ID", value=player_id),
                            client.V1EnvVar(name="MONSTER_NAME", value=pod_name),
                            client.V1EnvVar(
                                name="SERVICE_PORT", value=str(service_port)
                            ),
                            client.V1EnvVar(name="HEALTHY", value="true"),
                        ],
                        liveness_probe=client.V1Probe(
                            http_get=client.V1HTTPGetAction(
                                path="/healthz", port=service_port
                            ),
                            initial_delay_seconds=3,
                            period_seconds=3,
                        ),
                        readiness_probe=client.V1Probe(
                            http_get=client.V1HTTPGetAction(
                                path="/healthz", port=service_port
                            ),
                            initial_delay_seconds=3,
                            period_seconds=3,
                        ),
                    )
                ],
                node_name="minikube",
            ),
        )

        self.v1.create_namespaced_pod(namespace=namespace, body=pod_manifest)
        return self.expose_pod_port(pod_name, namespace, service_port)

    def expose_pod_port(self, pod_name, namespace, service_port):
        service_name = f"{pod_name}-state-service"
        service_spec = client.V1Service(
            metadata=client.V1ObjectMeta(name=service_name),
            spec=client.V1ServiceSpec(
                selector={"monster-name": pod_name},
                type="LoadBalancer",
                ports=[
                    client.V1ServicePort(port=service_port, target_port=service_port)
                ],
            ),
        )

        service = self.v1.create_namespaced_service(
            namespace=namespace, body=service_spec
        )
        return service.spec.ports[0].node_port

    def delete_pod(self, pod_name, namespace):
        print(f"Deleting pod '{pod_name}' in namespace '{namespace}'")
        self.v1.delete_namespaced_pod(name=pod_name, namespace=namespace)
        self.v1.delete_namespaced_service(
            name=f"{pod_name}-state-service", namespace=namespace
        )

    def get_pod(self, pod_name, namespace):
        pod = self.v1.read_namespaced_pod(name=pod_name, namespace=namespace)
        return pod

    def move_pod(self, pod_name, from_namespace, target_namespace, service_port):
        print(
            f"Moving '{pod_name}' to '{target_namespace}' listening on '{service_port}'"
        )
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
                liveness_probe=c.liveness_probe,
                readiness_probe=c.readiness_probe,
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
        self.v1.create_namespaced_pod(namespace=target_namespace, body=pod_manifest)
        self.expose_pod_port(pod_name, target_namespace, service_port)
        self.wait_for_pod_ready(pod_name, target_namespace)
        time.sleep(1)

    def kill_pod(self, player_id, pod_name, namespace, service_port):
        pod = self.get_pod(pod_name, namespace)
        self.delete_pod(pod_name, namespace)
        self.wait_for_pod_deletion(pod_name, namespace)

        containers = []
        for c in pod.spec.containers:
            clean_c = client.V1Container(
                name=c.name,
                image=c.image,
                ports=c.ports,
                env=[
                    client.V1EnvVar(name="DB_NAME", value=os.environ["DB_NAME"]),
                    client.V1EnvVar(name="DB_USER", value=os.environ["DB_USER"]),
                    client.V1EnvVar(
                        name="DB_PASSWORD", value=os.environ["DB_PASSWORD"]
                    ),
                    client.V1EnvVar(name="DB_HOST", value=DB_HOST),
                    client.V1EnvVar(name="DB_PORT", value=DB_PORT),
                    client.V1EnvVar(name="PLAYER_ID", value=player_id),
                    client.V1EnvVar(name="MONSTER_NAME", value=pod_name),
                    client.V1EnvVar(name="SERVICE_PORT", value=str(service_port)),
                    client.V1EnvVar(name="HEALTHY", value="false"),
                ],
                command=c.command,
                args=c.args,
                resources=c.resources,
                volume_mounts=[
                    vm
                    for vm in (c.volume_mounts or [])
                    if not vm.name.startswith("kube-api-access")
                ],
                liveness_probe=c.liveness_probe,
                readiness_probe=c.readiness_probe,
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

        print(f"Recreating pod '{pod_name}' but dead")
        self.v1.create_namespaced_pod(namespace=OUTSIDE_KEY, body=pod_manifest)
        self.expose_pod_port(pod_name, OUTSIDE_KEY, service_port)

    def get_ip(self):
        return subprocess.check_output(["minikube", "ip"], text=True).strip()

    def wait_for_pod_deletion(self, pod_name, namespace, timeout=60):
        print(f"Waiting for pod deletion of '{pod_name}'")
        for _ in range(timeout):
            try:
                self.v1.read_namespaced_pod(pod_name, namespace)
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
            pod = self.v1.read_namespaced_pod(pod_name, namespace)
            if pod.status.phase == "Running":
                conditions = pod.status.conditions or []
                ready = any(
                    c.type == "Ready" and c.status == "True" for c in conditions
                )
                if ready:
                    return

            time.sleep(2)

        raise TimeoutError(f"Pod {pod_name} start up timed out after {timeout} seconds")

    def is_pod_active(self, pod_name, namespace):
        pod = self.v1.read_namespaced_pod(pod_name, namespace)
        if pod.status.phase == "Running":
            conditions = pod.status.conditions or []
            ready = any(c.type == "Ready" and c.status == "True" for c in conditions)
            return ready
