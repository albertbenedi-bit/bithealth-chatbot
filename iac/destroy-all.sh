#!/bin/bash
# K3s destroy script for all services in iac folder
# By default, it preserves persistent data (PVCs).
# Use the --purge-data flag to delete all data and start completely fresh.
set -e

PURGE_DATA=false
if [[ "$1" == "--purge-data" ]]; then
  PURGE_DATA=true
fi

echo "Tearing down chatbot system from Kubernetes..."
echo "Deleting infrastructure services..."

# Selectively delete Postgres components to preserve the PVC by default.
# The --purge-data flag will handle deleting the PVC.
#kubectl delete -f postgres/postgres-deployment.yaml --ignore-not-found=true
#kubectl delete -f postgres/postgres-service.yaml --ignore-not-found=true
#kubectl delete -f postgres/postgres-secret.yaml --ignore-not-found=true

# Postgres
kubectl delete -f postgres/ --ignore-not-found

# Redis
kubectl delete -f redis/ --ignore-not-found

# Zookeeper
kubectl delete -f zookeeper/ --ignore-not-found

# Determine the current directory where this `./destroy-all.sh` script is located to make paths relative
# SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Kafka
# if [ "$PURGE_DATA" = true ]; then
#    echo "Purging Kafka topics..."
#    chmod +x "$SCRIPT_DIR/kafka/delete-topics.sh"
#    "$SCRIPT_DIR/kafka/delete-topics.sh"
# fi
kubectl delete -f kafka/ --ignore-not-found

echo "Deleting application services..."

# Backend Orchestrator
kubectl delete -f backend-orchestrator/ --ignore-not-found

# RAG Service
kubectl delete -f rag-service-2/ --ignore-not-found

# Appointment Management Agent
kubectl delete -f appointment-agent/ --ignore-not-found

# Debug Tools
kubectl delete -f debug-tools/ --ignore-not-found

# Frontend
kubectl delete -f frontend/ --ignore-not-found

# Auth Service
#kubectl delete -f auth-service/ --ignore-not-found

# Knowledge Base Service
#kubectl delete -f knowledge-base-service/ --ignore-not-found

# EHR Integration
#kubectl delete -f ehr-integration/ --ignore-not-found

# Communication Gateway
#kubectl delete -f communication-gateway/ --ignore-not-found

if [[ "$PURGE_DATA" == "true" ]]; then
  echo "---"
  echo "WARNING: Purging all persistent data (--purge-data flag was used)."
  
  # Find and delete PVCs in the 'data' namespace (for Postgres, Kafka, etc.)
  DATA_PVCS=$(kubectl get pvc -n data -o jsonpath='{.items[*].metadata.name}')
  if [[ -n "$DATA_PVCS" ]]; then
    echo "Deleting PersistentVolumeClaims in 'data' namespace: $DATA_PVCS"
    kubectl delete pvc $DATA_PVCS -n data --ignore-not-found=true
  else
    echo "No PersistentVolumeClaims found in 'data' namespace."
  fi
  
  # Also remove the underlying data on the host machine for a true purge.
  # IMPORTANT: Adjust this path to match the 'hostPath.path' in your postgres-volume.yaml
  # This path is for environments like Git Bash or WSL on Windows.
  HOST_DATA_PATH="/c/Users/User/kube-data/postgres"
  if [ -d "$HOST_DATA_PATH" ]; then
    echo "Deleting host data at: $HOST_DATA_PATH"
    rm -rf "$HOST_DATA_PATH"/*
  fi

  echo "Data purge complete."
else
  echo "---"
  echo "Persistent data (PVCs) have been preserved."
  echo "To delete all data, run this script with the --purge-data flag."
fi

echo "All services destroyed!"
