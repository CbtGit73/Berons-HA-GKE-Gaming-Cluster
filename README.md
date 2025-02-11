# Deploying a Highly Available Game Server Cluster on GKE with Agones
### What is Agones?

Agones provides a plug-and-play solution for deploying and managing game servers on Kubernetes. It simplifies the process of provisioning and scaling game servers by abstracting it's CRD's behind a well written operator. This allows infrastructure teams to focus on simple requirements, without needing to manage complex networking or manual server scaling.

Key features
- **Simplified Deployment** – Deploy game servers with minimal configuration, specifying only the **image, ports, and storage** needed.
- **Dynamic Scaling** – Agones manages **replica scaling**, ensuring game servers are available as player demand fluctuates.
- **Automated Port Management** – Dynamically assigns node ports, enabling direct connections to servers from their respective hosts without randomized routing.
- **API Integration** – Can be integrated with APIs to handle matchmaking and routing logic for game server allocation.

In short...
Agones offers a ready-to-use framework for hosting almost any kind of game server while leveraging the scalability and automation of cloud computing with minimal setup

Read the Well written Official Documentation here:
- https://agones.dev/site/docs/
- https://agones.dev/site/docs/getting-started/create-fleet/
- https://agones.dev/site/docs/installation/install-agones/helm/

---
### Deployment Steps

#### Step 1: Properly configure your underlying cluster

Ensure that your Kubernetes cluster has private nodes disabled `enable_private_nodes = false`. This allows Agones' networking CRDs to correctly assign node ports to each GameServer pod in your deployments.

This setup provides each GameServer with a unique, directly requestable ID, rather than relying on round-robin load balancing for request distribution. It can likely be integrated with an API that manages routing logic to dynamically allocate and direct traffic to the appropriate GameServer.

``` python
  private_cluster_config {
    enable_private_endpoint = false
    enable_private_nodes    = false #sometimes true
    master_ipv4_cidr_block  = "172.16.0.0/28"
  }
```
*Upon use of `kubectl get node -o wide` you should see an external address for your nodes.*

#### Step 2: Create a Firewall Rule for Game Server Traffic

Before deploying game servers with Agones, we need to configure a firewall rule that allows incoming UDP traffic to reach the Kubernetes cluster's nodes. This ensures that game clients can connect to the game servers hosted within the cluster.

```python
#Game-Server-Health-and-traffic
resource "google_compute_firewall" "game-cluster" {
  name        = "galaxy-grants-wandering-star"
  network     = var.network.name
  allow {
    protocol = "udp"
    ports    = ["7000-8000"]
  }

  source_ranges = ["0.0.0.0/0"]
  depends_on = [ google_compute_network.net-1 ]
}
#>>>
```

#### Step 3: Installing the operator through Helm

After setting up the firewall rules, you need to **install and deploy Agones** in your Kubernetes cluster using Helm. This step ensures that the **Agones CRDs, controllers, and networking components** are properly configured.

Commands:
```shell
helm repo add agones https://agones.dev/chart/stable
helm repo update
helm install my-release --namespace agones-system --create-namespace agones/agones
```
Now we can deploy game severs to the default namespace!

Verify correct instillation using the following command:
```shell
User@Caranthir MINGW64 /c/terraform/anton/module-practice/02-game-servers/test
$ kubectl get pods -n agones-system
NAME                                 READY   STATUS    RESTARTS   AGE
agones-allocator-6c6d8b7549-4drb2    1/1     Running   0          14m
agones-allocator-6c6d8b7549-cssdp    1/1     Running   0          14m
agones-allocator-6c6d8b7549-tsmn7    1/1     Running   0          14m
agones-controller-5b5c58c7d9-f9dvz   1/1     Running   0          14m
agones-controller-5b5c58c7d9-rqbx2   1/1     Running   0          14m
agones-extensions-8bdfd6bb5-g7k4j    1/1     Running   0          14m
agones-extensions-8bdfd6bb5-h99s6    1/1     Running   0          14m
agones-ping-7b766cc5db-5552l         1/1     Running   0          14m
agones-ping-7b766cc5db-cvl7s         1/1     Running   0          14m

```

---
##### Basic Server YAML Setup 

My Below Yaml Templates serve as a configurable example for templating servers within this operator. I designed this by editing the template found in the documentation. I integrated the tools I already had existing in my environments.

Through modifying the below takeaways this YAML example can be configured to host any type of game sever.

Key Takeaways:
- Define `containerPort` for the pods and the service to match the port request of your specific game server image.
- Change the `mountPath` in volume mounts to match the expected data paths for your server image of choice. *In my example the default test path for server data is `/home/Agones`*
- Make sure your configured service is set to translate UDP traffic

Deployment YAML Template
```python
apiVersion: agones.dev/v1
kind: Fleet
metadata:
  name: type-a
  namespace: default  # Change if needed
spec:
  replicas: 2
  template:
    metadata:
      labels:
        app: type-a
    spec:
      ports:
      - name: default
        containerPort: 7654
        portPolicy: Dynamic
      template:
        spec:
          containers:
          - name: simple-game-server
            image: us-docker.pkg.dev/agones-images/examples/simple-game-server:0.36
            volumeMounts:          
            - name: orbiter-module
              mountPath: /home/Agones
          volumes:
          - name: orbiter-module
            persistentVolumeClaim:
              claimName: orbiter-module
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 25%
      maxUnavailable: 25%
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: orbiter-module
  namespace: default
spec:
  accessModes: ["ReadWriteMany"]
  resources:
    requests:
      storage: 1Gi
  storageClassName: "bordeaux"
```

Allocation YAML Which Enables Dynamic Port Mapping to Host nodes Containing `type-a` 
```python
apiVersion: allocation.agones.dev/v1
kind: GameServerAllocation
metadata:
  name: alligator
  namespace: default  # Change if needed
spec:
  selectors:
  - matchLabels:
      agones.dev/fleet: type-a  # Match available GameServers in the Fleet
```

---
#### Step 4 : Executing the deployment of a server fleet

If using my repository, simply apply the test folder to deploy the Agones fleet and observe the results. 

`kubectl apply -f test/`
Use the below commands and observe rhe below outputs from a successful deployment.
``` shell
User@Caranthir MINGW64 /c/terraform/anton/module-practice/02-game-servers
$ kubectl get fleet -n default
NAME     SCHEDULING   DESIRED   CURRENT   ALLOCATED   READY   AGE
type-a   Packed       2         2         0           2       48s

User@Caranthir MINGW64 /c/terraform/anton/module-practice/02-game-servers
$ kubectl get gameservers -n default
NAME                 STATE   ADDRESS       PORT   NODE                                             AGE
type-a-tsnhl-57cvh   Ready   34.32.70.90   7308   gke-atreides-war-fleet-sardaukar-257007bd-75fv   3s
type-a-tsnhl-ggjwp   Ready   34.32.70.90   7972   gke-atreides-war-fleet-sardaukar-257007bd-75fv   2m33s
type-a-tsnhl-rnccn   Ready   34.32.70.90   7424   gke-atreides-war-fleet-sardaukar-257007bd-75fv   3s
# Notice addresses on our pods
```

###### Validating Server Functionality
Within the test directory, you'll find a Python script (test-script.py) designed to send a request to the deployed game server and validate its response.

Edit & Run the script to initiate a test request on our live servers:
```python
import socket

server_ip = "34.32.70.90" # Change to IP address assigned to pod
server_port = 7972 # Change to the port of the server you want to test
message = "Hello from outside"

# Create UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

try:
    # Send the message
    print(f"Sending: '{message}' to {server_ip}:{server_port}")
    sock.sendto(message.encode(), (server_ip, server_port))

    # Set timeout to avoid hanging
    sock.settimeout(5)  # 5 seconds timeout

    # Try to receive a response (if the server replies)
    try:
        response, addr = sock.recvfrom(1024)  # Buffer size of 1024 bytes
        print(f"Received from {addr}: {response.decode()}")
    except socket.timeout:
        print("No response received (you might be ugly)")

finally:
    sock.close()
    print("Connection closed.")


```

#### Step 5 : Testing 

Use the below Command and observe the below output from a successful request:
``` shell
User@Caranthir MINGW64 /c/terraform/anton/module-practice/02-game-servers
$ python test-script.py
Sending: 'Hello from outside' to 34.32.70.90:7972
Received from ('34.32.70.90', 7972): ACK: Hello from outside

Connection closed.
```


And now we have a sure fire way of building out many varieties of gaming server.  We need only change images and container ports per new configuration. 

Feel free to experiment and share your learnings.

---
