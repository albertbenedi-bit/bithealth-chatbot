#!/bin/bash


set -e

SERVICE_NAME="frontend"
IMAGE_NAME="frontend"
DEFAULT_TAG="latest"
DOCKERFILE_PATH="../../frontend"

TAG=${1:-$DEFAULT_TAG}
REGISTRY=${2:-"localhost:5000"}
PUSH=${3:-true}

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Frontend Docker Image Build ===${NC}"
echo -e "${YELLOW}Service:${NC} $SERVICE_NAME"
echo -e "${YELLOW}Tag:${NC} $TAG"
echo -e "${YELLOW}Registry:${NC} ${REGISTRY:-"(local only)"}"
echo -e "${YELLOW}Push:${NC} $PUSH"
echo ""

if [ -n "$REGISTRY" ]; then
    FULL_IMAGE_NAME="$REGISTRY/$IMAGE_NAME:$TAG"
else
    FULL_IMAGE_NAME="$IMAGE_NAME:$TAG"
fi

echo -e "${BLUE}Building Docker image: $FULL_IMAGE_NAME${NC}"

cd "$DOCKERFILE_PATH"

echo -e "${YELLOW}Running docker build...${NC}"
docker build -t "$FULL_IMAGE_NAME" .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Docker image built successfully: $FULL_IMAGE_NAME${NC}"
else
    echo -e "${RED}❌ Docker build failed${NC}"
    exit 1
fi

if [ "$PUSH" = "true" ] || [ "$PUSH" = "1" ]; then
    if [ -z "$REGISTRY" ]; then
        echo -e "${RED}❌ Cannot push: No registry specified${NC}"
        exit 1
    fi
    
    echo -e "${YELLOW}Pushing image to registry...${NC}"
    docker push "$FULL_IMAGE_NAME"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Image pushed successfully to registry${NC}"
    else
        echo -e "${RED}❌ Failed to push image to registry${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${BLUE}=== Image Information ===${NC}"
docker images | grep "$IMAGE_NAME" | head -5

echo ""
echo -e "${GREEN}=== Build Complete ===${NC}"
echo -e "${YELLOW}Image:${NC} $FULL_IMAGE_NAME"
echo -e "${YELLOW}Usage:${NC} docker run -p 3000:80 $FULL_IMAGE_NAME"
echo ""
echo -e "${BLUE}=== Script Usage ===${NC}"
echo "  $0 [TAG] [REGISTRY] [PUSH]"
echo ""
echo "Examples:"
echo "  $0                                    # Build with 'latest' tag"
echo "  $0 v1.0.0                           # Build with 'v1.0.0' tag"
echo "  $0 v1.0.0 my-registry.com          # Build with registry prefix"
echo "  $0 v1.0.0 my-registry.com true     # Build and push to registry"
