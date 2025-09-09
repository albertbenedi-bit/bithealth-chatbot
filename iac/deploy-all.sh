#!/bin/bash


set -e

echo "Deploying healthcare chatbot system to Kubernetes..."

# Ensure namespaces exist without failing if they are already there
kubectl create namespace general-chatbot-app --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace data --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace rag-app --dry-run=client -o yaml | kubectl apply -f -

echo "Deploying infrastructure services..."
kubectl apply -f postgres/
kubectl apply -f redis/
kubectl apply -f zookeeper/
kubectl apply -f kafka/
# The debug-tools directory contains manifests for on-demand troubleshooting pods.
# These are not deployed by default. Deploy them manually when needed.
# Example: kubectl apply -f debug-tools/generic-debug-pod.yaml
echo "Waiting for infrastructure services to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres -n data --timeout=300s || echo "Postgres not ready"
kubectl wait --for=condition=ready pod -l app=redis -n data --timeout=300s || echo "Redis not ready"
kubectl wait --for=condition=ready pod -l app=zookeeper -n data --timeout=300s || echo "Zookeeper not ready"
kubectl wait --for=condition=ready pod -l app=kafka -n data --timeout=300s || echo "Kafka not ready"

# Determine the current directory where this `./deploy-all.sh` script is located to make paths relative
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

echo "Initializing Kafka topics..."
chmod +x "$SCRIPT_DIR/kafka/init-topics.sh"
"$SCRIPT_DIR/kafka/init-topics.sh"

echo "--- Database Initialization ---"
echo "Starting temporary port-forward to initialize database..."
# Start port-forward in the background, redirecting its output
kubectl port-forward svc/my-rag-postgres-postgresql 5432:5432 -n data >/dev/null 2>&1 &
PG_FWD_PID=$!

# Ensure the port-forward process is killed when the script exits
trap "echo 'Stopping postgres port-forward...'; kill $PG_FWD_PID" EXIT

echo "Waiting for port-forward to establish... (PID: $PG_FWD_PID)"
sleep 5 # Give a few seconds for the connection to be ready

echo "Running database schema initialization scripts..."
python "$SCRIPT_DIR/postgres/db_init_schema.py"
python "$SCRIPT_DIR/postgres/appointment_schema_init.py"

echo "Running data ingestion script..."
python "$SCRIPT_DIR/postgres/ingest_data.py"

echo "Database initialization complete. Stopping temporary port-forward."
kill $PG_FWD_PID
trap - EXIT # Clear the trap

echo "Deploying application services..."
kubectl apply -f frontend/
kubectl apply -f backend-orchestrator/
kubectl apply -f rag-service-2/
kubectl apply -f appointment-agent/
# kubectl apply -f auth-service/ || echo "Auth service deployment skipped"
# kubectl apply -f knowledge-base-service/ || echo "Knowledge base service deployment skipped"
# kubectl apply -f ehr-integration/ || echo "EHR integration deployment skipped"
# kubectl apply -f communication-gateway/ || echo "Communication gateway deployment skipped"

echo "Deployment complete!"
echo "--------------------------------------------------"
echo "Waiting for application services to be ready..."
kubectl wait --for=condition=ready pod -l app=frontend -n general-chatbot-app --timeout=120s
kubectl wait --for=condition=ready pod -l app=backend-orchestrator -n general-chatbot-app --timeout=120s
kubectl wait --for=condition=ready pod -l app=rag-service-2 -n rag-app --timeout=300s
kubectl wait --for=condition=ready pod -l app=appointment-agent -n general-chatbot-app --timeout=300s

echo "All services are deployed and ready."
echo ""
echo "To access the services locally, run these commands in separate terminals:"
echo "  - Frontend:             kubectl port-forward svc/frontend-service 3000:80 -n general-chatbot-app"
echo "  - Backend Orchestrator: kubectl port-forward svc/backend-orchestrator 8000:8000 -n general-chatbot-app"
echo "  - Appointment Agent:    kubectl port-forward svc/appointment-agent 8001:8000 -n general-chatbot-app"
echo "  - RAG Service 2:        kubectl port-forward svc/rag-service-2 8002:8000 -n rag-app"
echo "--------------------------------------------------"

echo "Starting port-forward for the frontend service now."
echo "The application will be available at http://localhost:3000"
echo "Press Ctrl+C to stop this script and the port-forward."
kubectl port-forward svc/frontend-service 3000:80 -n general-chatbot-app
#kubectl port-forward svc/backend-orchestrator 8000:8000 -n general-chatbot-app
#kubectl port-forward svc/appointment-agent 8001:8000 -n general-chatbot-app
#kubectl port-forward svc/rag-service-2 8002:8000 -n rag-app
#kubectl port-forward svc/my-rag-postgres-postgresql 5432:5432 -n data
#kubectl port-forward svc/kafka 9092:9092 -n data
#kubectl port-forward svc/redis 6379:6379 -n data