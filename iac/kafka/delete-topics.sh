#!/bin/bash

# This script will delete all Kafka topics
echo "Deleting Kafka topics..."

echo "Waiting for Kafka to be ready..."
until kubectl exec -n data $(kubectl get pod -l app=kafka -n data -o jsonpath='{.items[0].metadata.name}') -- kafka-topics.sh --list --bootstrap-server localhost:9092 &> /dev/null; do
    echo "Waiting for Kafka to be ready..."
    sleep 5
done

# Delete all topics
TOPICS=(
    "general-info-requests"
    "general-info-responses"
    "appointment-agent-requests"
    "appointment-agent-responses"
)

for topic in "${TOPICS[@]}"; do
    echo "Deleting topic: $topic"
    kubectl exec -n data $(kubectl get pod -l app=kafka -n data -o jsonpath='{.items[0].metadata.name}') -- \
        kafka-topics.sh --delete --topic "$topic" --bootstrap-server localhost:9092 || echo "Topic $topic not found or already deleted"
done

echo "Kafka topics deleted successfully"
