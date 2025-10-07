#!/bin/bash
# Build and push OpsAgent container image to Quay.io

set -e

# Configuration
IMAGE_NAME="quay.io/rbrhssa/ops-agents"
TAG="${1:-latest}"  # Use argument or default to 'latest'

echo "🔨 Building OpsAgent container image..."
podman build -f Containerfile -t ${IMAGE_NAME}:${TAG} .

echo "📦 Tagging image as latest..."
if [ "$TAG" != "latest" ]; then
    podman tag ${IMAGE_NAME}:${TAG} ${IMAGE_NAME}:latest
fi

echo "🚀 Pushing to Quay.io..."
podman push ${IMAGE_NAME}:${TAG}

if [ "$TAG" != "latest" ]; then
    podman push ${IMAGE_NAME}:latest
fi

echo "✅ Build and push complete!"
echo "Image: ${IMAGE_NAME}:${TAG}"

# Display image info
echo ""
echo "📋 Image details:"
podman images | grep ops-agents
