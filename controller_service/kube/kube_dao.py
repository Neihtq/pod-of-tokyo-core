import subprocess
from collections import defaultdict

from kubernetes import client, config
from kubernetes.client.rest import ApiException

NAMESPACE = "default"


class KubeDao:
    def list_all_nodes(self):
        node_list = self.client.list_node()
        nodes = []
        for n in node_list.items:
            node = {"name": n.metadata.name}

            if n.status.conditions:
                for condition in n.status.conditions:
                    node[condition.type] = condition.status

            if n.metadata.labels and "location" in n.metadata.labels:
                node["location"] = n.metadata.labels["location"]
            else:
                node["location"] = None
            nodes.append(node)

        print(f"All listed nodes:\n{nodes}")
        return nodes

    def spawn_nodes(self, name_pairs):
        subprocess.run(
            ["minikube", "start", "--nodes", str(len(name_pairs))], check=True
        )
        config.load_kube_config()
        self.client = client.CoreV1Api()

        nodes = self.client.list_node().items
        for i, node in enumerate(nodes):
            if i >= len(name_pairs):
                break
            body = {
                "metadata": {
                    "labels": {
                        "location": name_pairs[i],
                    }
                }
            }
            self.client.patch_node(node.metadata.name, body)

    def delete_node(self, node_name):
        subprocess.run(["minikube", "node", "delete", node_name])

    def delete_all_nodes(self):
        subprocess.run(["minikube", "delete", "--all"], check=True)

    def list_all_pods(self):
        pods = self.client.list_pod_for_all_namespaces().items

        pods_by_nodes = defaultdict(list)
        for pod in pods:
            node_name = pod.spec.node_name
            if node_name:
                pods_by_nodes[node_name].append(pod.metadata.name)

        return pods_by_nodes

    def create_pod(
        self,
        pod_name,
        node_name,
        image="nginx",
        container_port=80,
    ):
        print(f"Creating pod '{pod_name}' in node '{node_name}")
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
                node_name=node_name,
            ),
        )

        self.client.create_namespaced_pod(namespace=NAMESPACE, body=pod_manifest)
        node_port = self.expose_pod_port(pod_name)
        return node_port

    def expose_pod_port(self, pod_name, node_port=None):
        service_name = f"{pod_name}-state-service"
        service_spec = client.V1Service(
            metadata=client.V1ObjectMeta(name=service_name),
            spec=client.V1ServiceSpec(
                selector={"monster-name": pod_name},
                type="NodePort",
                ports=[
                    client.V1ServicePort(port=80, target_port=80, node_port=node_port)
                ],
            ),
        )

        service = self.client.create_namespaced_service(
            namespace=NAMESPACE, body=service_spec
        )
        return service.spec.ports[0].node_port

    def delete_pod(self, pod_name):
        self.client.delete_namespaced_pod(name=pod_name, namespace=NAMESPACE)

    def get_pod(self, pod_name):
        pod = self.client.read_namespaced_pod(name=pod_name, namespace=NAMESPACE)
        return pod

    def move_pod(self, pod_name, target_node):
        pod = self.get_pod(pod_name)
        self.delete_pod(pod_name)

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
                    for v in (pod.spec.vollumes or [])
                    if not v.name.startswith("kube-api-access")
                ],
                node_name=target_node,
            ),
        )

        self.client.create_namespaced_pod(namespace=NAMESPACE, body=pod_manifest)

    def get_ip(self):
        return subprocess.check_output(["minikube", "ip"], text=True).strip()
