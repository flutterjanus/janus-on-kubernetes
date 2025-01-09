# Deploying Janus on Kubernetes: A Comprehensive Guide

This document provides a successful approach to deploying Janus on Kubernetes effectively.

---

## Generating Multi-Port Configurations Using `port-ranger`

### Generate Multi-Port UDP Routes YAML
To generate UDP route configurations with multiple ports:
```bash
# Note: UDP routes cannot exceed 16 due to Kubernetes' limitation on UDP routes
python3 port-ranger.py ./udpRoutes.yaml janus 10000 11000 UDP ./udp_routes_generated.yaml --chunk-size 16
```

### Generate Multi-Port Service YAML
To create service configurations for multiple ports:
```bash
python3 port-ranger.py ./service.yaml janus 10000 11000 UDP ./service_generated.yaml
```

---

## Prerequisites

### Environment Setup
- Local deployment was tested on **minikube** with the Envoy Gateway API.
- Ensure the following are installed and properly set up:
  - **Minikube cluster**
  - **Envoy CRD (Custom Resource Definitions)**

### Assumptions
This guide uses a UDP port range of **10000-11000**, providing 1000 UDP ports. Under the assumption that each user utilizes 4 UDP ports for media traversal, this configuration supports up to **250 concurrent users**. To support more users, increase the port range using `port-ranger`.

---

## Quickstart

### Step 1: Initialize ConfigMap for Janus
Run the following script to initialize the Janus configuration in config-map:
```bash
./update_conf.sh
```

### Step 2: Apply Kubernetes YAML Configurations
Apply the configurations in the following order:
```bash
kubectl apply -f gatewayClass.yaml
kubectl apply -f gateway.yaml
kubectl apply -f btp.yaml
kubectl apply -f httpRoutes.yaml
kubectl apply -f udp_routes_generated.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service_generated.yaml
```

---

## Testing the Deployment

### Update Local DNS
Update your `/etc/hosts` file with the following entries:
```
# /etc/hosts
127.0.0.1 janus-0.example.local
127.0.0.1 janus-1.example.local
127.0.0.1 janus-2.example.local
```

### Verify Access
If everything is correctly configured, you can access the Janus server using the following endpoints:

#### REST API
```bash
curl http://janus-0.example.local/rest/janus/info
```

#### WebSocket
```
http://janus-0.example.local/ws
```

#### Admin WebSocket
```
http://janus-0.example.local/admin-ws
```

---

## Notes
- Ensure the port range used matches the one specified in your configuration.
- For larger-scale deployments, adjust the port range and user calculations accordingly.

By following this guide, you should be able to successfully deploy and test Janus on Kubernetes.

