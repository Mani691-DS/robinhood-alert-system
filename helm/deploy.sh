#!/usr/bin/env bash
# Master deployment script for Minikube.
# Run from the project root: bash helm/deploy.sh
set -euo pipefail

NAMESPACE="stock-alert"
STRIMZI_NS="strimzi-system"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# ── 1. Minikube ────────────────────────────────────────────────────────────────
echo "==> Checking Minikube..."
if ! minikube status | grep -q "Running"; then
  echo "Starting Minikube (4 CPUs, 6 GB RAM)..."
  minikube start --cpus=4 --memory=6144
fi

# ── 2. Strimzi operator ────────────────────────────────────────────────────────
echo ""
echo "==> Installing Strimzi operator..."
helm repo add strimzi https://strimzi.io/charts/ --force-update
helm upgrade --install strimzi-operator strimzi/strimzi-kafka-operator \
  --namespace "$STRIMZI_NS" \
  --create-namespace \
  --wait

# ── 3. Application namespace ───────────────────────────────────────────────────
echo ""
echo "==> Creating namespace $NAMESPACE..."
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

# ── 4. Kafka cluster (KRaft via Strimzi) ──────────────────────────────────────
echo ""
echo "==> Deploying Kafka cluster (KRaft, single-node)..."
kubectl apply -f "$SCRIPT_DIR/strimzi/kafka-cluster.yaml" -n "$NAMESPACE"

echo "Waiting for Kafka to become Ready (up to 5 minutes)..."
kubectl wait kafka/stock-alert-kafka \
  --for=condition=Ready \
  --timeout=300s \
  -n "$NAMESPACE"

# ── 5. Kafka topics ────────────────────────────────────────────────────────────
echo ""
echo "==> Creating Kafka topics..."
kubectl apply -f "$SCRIPT_DIR/strimzi/kafka-topics.yaml" -n "$NAMESPACE"

# ── 6. Redis ───────────────────────────────────────────────────────────────────
echo ""
echo "==> Installing Redis..."
helm repo add bitnami https://charts.bitnami.com/bitnami --force-update
helm upgrade --install redis bitnami/redis \
  -f "$SCRIPT_DIR/redis/values.yaml" \
  --namespace "$NAMESPACE" \
  --wait

# ── 7. Schema Registry ────────────────────────────────────────────────────────
echo ""
echo "==> Deploying Schema Registry..."
kubectl apply -f "$SCRIPT_DIR/schema-registry/manifest.yaml" -n "$NAMESPACE"

# ── 8. Build Docker images inside Minikube ────────────────────────────────────
echo ""
echo "==> Pointing Docker CLI at Minikube's daemon..."
eval "$(minikube docker-env)"

echo "Building images (build context: project root)..."
docker build -f "$ROOT_DIR/backend/market-simulator/Dockerfile"      "$ROOT_DIR" -t market-simulator:latest
docker build -f "$ROOT_DIR/backend/alert-service/Dockerfile"         "$ROOT_DIR" -t alert-service:latest
docker build -f "$ROOT_DIR/backend/price-monitor/Dockerfile"         "$ROOT_DIR" -t price-monitor:latest
docker build -f "$ROOT_DIR/backend/notification-service/Dockerfile"  "$ROOT_DIR" -t notification-service:latest
docker build -f "$ROOT_DIR/backend/dashboard-service/Dockerfile"     "$ROOT_DIR" -t dashboard-service:latest

# ── 9. Deploy all 5 services via Helm chart ───────────────────────────────────
echo ""
echo "==> Installing stock-alert Helm chart..."
helm upgrade --install stock-alert "$SCRIPT_DIR/stock-alert" \
  --namespace "$NAMESPACE" \
  --wait

echo ""
echo "==> Waiting for rollouts..."
kubectl rollout status deployment/stock-alert-alert-service     -n "$NAMESPACE" --timeout=120s
kubectl rollout status deployment/stock-alert-dashboard-service -n "$NAMESPACE" --timeout=120s

# ── Done ──────────────────────────────────────────────────────────────────────
MINIKUBE_IP=$(minikube ip)
echo ""
echo "========================================="
echo " Deployment complete!"
echo "========================================="
echo ""
echo "  Alert Service API : http://${MINIKUBE_IP}:30001/docs"
echo "  Dashboard         : http://${MINIKUBE_IP}:30002"
echo ""
echo "Or port-forward for localhost access:"
echo "  kubectl port-forward svc/stock-alert-alert-service     8001:8001 -n $NAMESPACE"
echo "  kubectl port-forward svc/stock-alert-dashboard-service 8002:8002 -n $NAMESPACE"
echo ""
echo "Helm release status:"
echo "  helm status stock-alert -n $NAMESPACE"
echo ""
echo "Check pod status:"
echo "  kubectl get pods -n $NAMESPACE"
