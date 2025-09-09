#!/bin/bash

# Stop on first error
set -e

# --- Configuration ---
IMAGE_NAME="k8s-debug-tools"
DEFAULT_TAG="v1.0.0"
# The Dockerfile is located in the current directory
DOCKERFILE_PATH="."

# --- Command Line Arguments ---
TAG=${1:-$DEFAULT_TAG}
# Default registry is localhost:5000
REGISTRY=${2:-"localhost:5000"}
PUSH=${3:-true}

# --- Colors for logging ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# --- Script Logic ---
echo -e "${BLUE}=== Kubernetes Debug Tools Image Build ===${NC}"
echo -e "${YELLOW}Image:${NC} $IMAGE_NAME"
echo -e "${YELLOW}Tag:${NC} $TAG"
echo -e "${YELLOW}Registry:${NC} ${REGISTRY:-"(local only)"}"
echo -e "${YELLOW}Push:${NC} $PUSH"
echo ""

# Construct the full image name
if [ -n "$REGISTRY" ]; then
    FULL_IMAGE_NAME="$REGISTRY/$IMAGE_NAME:$TAG"
else
    FULL_IMAGE_NAME="$IMAGE_NAME:$TAG"
fi

echo -e "${BLUE}Building Docker image: $FULL_IMAGE_NAME${NC}"

# The script is expected to be run from the iac/debug-tools directory
echo -e "${YELLOW}Running docker build...${NC}"
docker build -t "$FULL_IMAGE_NAME" "$DOCKERFILE_PATH"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Docker image built successfully: $FULL_IMAGE_NAME${NC}"
else
    echo -e "${RED}❌ Docker build failed${NC}"
    exit 1
fi

# Push the image if requested
if [ "$PUSH" = "true" ] || [ "$PUSH" = "1" ]; then
    if [ -z "$REGISTRY" ]; then
        echo -e "${RED}❌ Cannot push: No registry specified${NC}"
        exit 1
    fi

    # No need to tag if built with FULL_IMAGE_NAME

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
echo -e "${GREEN}=== Build Complete ===${NC}"
echo -e "${YELLOW}Image:${NC} $FULL_IMAGE_NAME"