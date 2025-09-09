#!/bin/bash

# Wait for Kafka to be ready
echo "Waiting for Kafka to be ready..."
until kubectl exec -n data $(kubectl get pod -l app=kafka -n data -o jsonpath='{.items[0].metadata.name}') -- kafka-topics.sh --list --bootstrap-server localhost:9092; do
    echo "Waiting for Kafka to be ready..."
    sleep 5
done

# Create topics with proper configurations
echo "Creating Kafka topics..."

# General info topics (already exist but recreating for consistency)
kubectl exec -n data $(kubectl get pod -l app=kafka -n data -o jsonpath='{.items[0].metadata.name}') -- \
    kafka-topics.sh --create --if-not-exists \
    --topic general-info-requests \
    --partitions 3 \
    --replication-factor 1 \
    --bootstrap-server localhost:9092

kubectl exec -n data $(kubectl get pod -l app=kafka -n data -o jsonpath='{.items[0].metadata.name}') -- \
    kafka-topics.sh --create --if-not-exists \
    --topic general-info-responses \
    --partitions 3 \
    --replication-factor 1 \
    --bootstrap-server localhost:9092

# Appointment agent topics
kubectl exec -n data $(kubectl get pod -l app=kafka -n data -o jsonpath='{.items[0].metadata.name}') -- \
    kafka-topics.sh --create --if-not-exists \
    --topic appointment-agent-requests \
    --partitions 3 \
    --replication-factor 1 \
    --bootstrap-server localhost:9092

kubectl exec -n data $(kubectl get pod -l app=kafka -n data -o jsonpath='{.items[0].metadata.name}') -- \
    kafka-topics.sh --create --if-not-exists \
    --topic appointment-agent-responses \
    --partitions 3 \
    --replication-factor 1 \
    --bootstrap-server localhost:9092

echo "Kafka topics created successfully"

# List all topics to verify
echo "Listing all topics:"
kubectl exec -n data $(kubectl get pod -l app=kafka -n data -o jsonpath='{.items[0].metadata.name}') -- \
    kafka-topics.sh --list --bootstrap-server localhost:9092
