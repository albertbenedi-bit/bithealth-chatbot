#!/bin/bash


set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

VERSION="v1.0.0"
REGISTRY="localhost:5000"

# List of services and their build paths
# Comment out any service to exclude from build/test
SERVICES=(
    "frontend:iac/frontend"
    "backend-orchestrator:iac/backend-orchestrator"
    'rag-service-2:iac/rag-service-2'
    "appointment-agent:iac/appointment-agent"
    #"rag-service:iac/rag-service"
    #"auth-service:iac/auth-service"
    #"knowledge-base-service:iac/knowledge-base-service"
    #"ehr-integration:iac/ehr-integration"
    #"communication-gateway:iac/communication-gateway"
)

echo -e "${BLUE}=== PV Chatbot Build and Test ===${NC}"

for entry in "${SERVICES[@]}"; do
    SERVICE_NAME="${entry%%:*}"
    SERVICE_PATH="${entry#*:}"
    echo -e "${YELLOW}Building ${SERVICE_NAME}...${NC}"
    (
        cd "$SERVICE_PATH"
        ./build-image.sh "${VERSION}"
    )
    # Tag the image, but allow it to fail in case the sub-script already tagged it.
    docker tag "${SERVICE_NAME}:${VERSION}" "${REGISTRY}/${SERVICE_NAME}:${VERSION}" || true
    docker push "${REGISTRY}/${SERVICE_NAME}:${VERSION}"

done

echo -e "${GREEN}✅ All builds completed successfully!${NC}"

echo -e "${BLUE}=== Running Basic Tests ===${NC}"
echo -e "${YELLOW}Testing if images were created...${NC}"

for entry in "${SERVICES[@]}"; do
    SERVICE_NAME="${entry%%:*}"
    if docker images | grep -q "${REGISTRY}/${SERVICE_NAME}.*${VERSION}"; then
        echo -e "${GREEN}✅ ${SERVICE_NAME} image pushed to local registry${NC}"
    else
        echo -e "${RED}❌ ${SERVICE_NAME} image not found in local registry${NC}"
        exit 1
    fi
done

echo -e "${GREEN}✅ All tests passed!${NC}"
