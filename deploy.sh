#!/bin/bash

# InternalTTS Docker Deployment Script
# This script helps deploy the InternalTTS application to a private Docker registry

set -e

# Configuration
REGISTRY_URL="${REGISTRY_URL:-your-registry.company.com}"
REGISTRY_PORT="${REGISTRY_PORT:-5000}"
IMAGE_NAME="${IMAGE_NAME:-internal-tts}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
FULL_IMAGE_NAME="${REGISTRY_URL}:${REGISTRY_PORT}/${IMAGE_NAME}:${IMAGE_TAG}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required environment variables are set
check_env() {
    if [[ -z "$REGISTRY_URL" || "$REGISTRY_URL" == "your-registry.company.com" ]]; then
        log_error "REGISTRY_URL environment variable must be set"
        log_info "Example: export REGISTRY_URL=registry.company.com"
        exit 1
    fi
}

# Build the Docker image
build_image() {
    log_info "Building Docker image..."
    docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" .
    log_info "Image built successfully: ${IMAGE_NAME}:${IMAGE_TAG}"
}

# Tag image for private registry
tag_image() {
    log_info "Tagging image for private registry..."
    docker tag "${IMAGE_NAME}:${IMAGE_TAG}" "${FULL_IMAGE_NAME}"
    log_info "Image tagged as: ${FULL_IMAGE_NAME}"
}

# Push image to private registry
push_image() {
    log_info "Pushing image to private registry..."
    docker push "${FULL_IMAGE_NAME}"
    log_info "Image pushed successfully to: ${FULL_IMAGE_NAME}"
}

# Login to private registry (if needed)
login_registry() {
    log_info "Attempting to login to private registry..."
    if ! docker login "${REGISTRY_URL}:${REGISTRY_PORT}"; then
        log_warn "Login failed. You may need to provide credentials manually."
        log_info "Run: docker login ${REGISTRY_URL}:${REGISTRY_PORT}"
        read -p "Press Enter to continue after logging in manually..."
    fi
}

# Pull and run from private registry
deploy_from_registry() {
    log_info "Deploying from private registry..."
    
    # Stop existing container if running
    if docker ps -q -f name=internal-tts-app | grep -q .; then
        log_info "Stopping existing container..."
        docker stop internal-tts-app
        docker rm internal-tts-app
    fi
    
    # Pull latest image
    log_info "Pulling latest image from registry..."
    docker pull "${FULL_IMAGE_NAME}"
    
    # Run the container
    log_info "Starting container..."
    docker run -d \
        --name internal-tts-app \
        -p 5000:5000 \
        -e TTS_APP_SECRET="${TTS_APP_SECRET:-change-me}" \
        -v "$(pwd)/data:/app/data" \
        -v "$(pwd)/audio:/app/audio" \
        --restart unless-stopped \
        "${FULL_IMAGE_NAME}"
    
    log_info "Container started successfully!"
    log_info "Application available at: http://localhost:5000"
}

# Main script logic
main() {
    case "${1:-build}" in
        "build")
            check_env
            build_image
            tag_image
            ;;
        "push")
            check_env
            build_image
            tag_image
            login_registry
            push_image
            ;;
        "deploy")
            check_env
            deploy_from_registry
            ;;
        "full")
            check_env
            build_image
            tag_image
            login_registry
            push_image
            deploy_from_registry
            ;;
        *)
            echo "Usage: $0 {build|push|deploy|full}"
            echo ""
            echo "Commands:"
            echo "  build  - Build and tag the Docker image"
            echo "  push   - Build, tag, and push to private registry"
            echo "  deploy - Pull and run from private registry"
            echo "  full   - Complete build, push, and deploy cycle"
            echo ""
            echo "Environment Variables:"
            echo "  REGISTRY_URL    - Private registry URL (required)"
            echo "  REGISTRY_PORT   - Registry port (default: 5000)"
            echo "  IMAGE_NAME      - Image name (default: internal-tts)"
            echo "  IMAGE_TAG       - Image tag (default: latest)"
            echo "  TTS_APP_SECRET  - Application secret key"
            echo ""
            echo "Example:"
            echo "  export REGISTRY_URL=registry.company.com"
            echo "  export TTS_APP_SECRET=your-secure-secret"
            echo "  $0 full"
            exit 1
            ;;
    esac
}

main "$@"
