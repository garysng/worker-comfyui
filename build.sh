#!/bin/bash

# ComfyUI Worker Build Script
# Build Docker image for ComfyUI handler with supervisord

set -e

# Configuration
IMAGE_NAME=${IMAGE_NAME:-"comfyui-worker"}
IMAGE_TAG=${IMAGE_TAG:-"latest"}
DOCKERFILE_PATH=${DOCKERFILE_PATH:-"deploy/Dockerfile"}
BUILD_CONTEXT=${BUILD_CONTEXT:-"."}
PLATFORM=${PLATFORM:-"linux/amd64"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# Help function
show_help() {
    cat << EOF
ComfyUI Worker Build Script

Usage: $0 [OPTIONS]

Options:
    -h, --help              Show this help message
    -n, --name NAME         Image name (default: comfyui-worker)
    -t, --tag TAG           Image tag (default: latest)
    -f, --file PATH         Dockerfile path (default: deploy/Dockerfile)
    -c, --context PATH      Build context (default: .)
    -p, --platform PLATFORM Build platform (default: linux/amd64)
    --no-cache              Build without cache
    --push                  Push image after build
    --multi-platform        Build for multiple platforms (linux/amd64,linux/arm64)

Environment Variables:
    IMAGE_NAME              Override default image name
    IMAGE_TAG               Override default image tag
    DOCKERFILE_PATH         Override default Dockerfile path
    BUILD_CONTEXT           Override default build context
    PLATFORM                Override default build platform

Examples:
    # Basic build
    ./build.sh

    # Build with custom name and tag
    ./build.sh -n my-comfyui -t v1.0.0

    # Build without cache
    ./build.sh --no-cache

    # Build and push
    ./build.sh --push

    # Multi-platform build
    ./build.sh --multi-platform

EOF
}

# Parse command line arguments
NO_CACHE=""
PUSH_IMAGE=""
MULTI_PLATFORM=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -n|--name)
            IMAGE_NAME="$2"
            shift 2
            ;;
        -t|--tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        -f|--file)
            DOCKERFILE_PATH="$2"
            shift 2
            ;;
        -c|--context)
            BUILD_CONTEXT="$2"
            shift 2
            ;;
        -p|--platform)
            PLATFORM="$2"
            shift 2
            ;;
        --no-cache)
            NO_CACHE="--no-cache"
            shift
            ;;
        --push)
            PUSH_IMAGE="true"
            shift
            ;;
        --multi-platform)
            MULTI_PLATFORM="true"
            PLATFORM="linux/amd64,linux/arm64"
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Validate inputs
if [ ! -f "$DOCKERFILE_PATH" ]; then
    log_error "Dockerfile not found: $DOCKERFILE_PATH"
    exit 1
fi

if [ ! -d "$BUILD_CONTEXT" ]; then
    log_error "Build context directory not found: $BUILD_CONTEXT"
    exit 1
fi

# Full image name
FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"

# Pre-build info
log_info "=== ComfyUI Worker Build ==="
log_info "Image: $FULL_IMAGE_NAME"
log_info "Dockerfile: $DOCKERFILE_PATH"
log_info "Context: $BUILD_CONTEXT"
log_info "Platform: $PLATFORM"
echo ""

# Check if Docker is available
if ! command -v docker >/dev/null 2>&1; then
    log_error "Docker is not installed or not in PATH"
    exit 1
fi

# Check if Docker daemon is running
if ! docker info >/dev/null 2>&1; then
    log_error "Docker daemon is not running"
    exit 1
fi

# Build command construction
BUILD_CMD="docker build"

if [ -n "$NO_CACHE" ]; then
    BUILD_CMD="$BUILD_CMD $NO_CACHE"
    log_info "Building without cache"
fi

if [ -n "$MULTI_PLATFORM" ]; then
    BUILD_CMD="docker buildx build --platform $PLATFORM"
    log_info "Building for multiple platforms: $PLATFORM"
    
    # Check if buildx is available
    if ! docker buildx version >/dev/null 2>&1; then
        log_error "Docker buildx is not available"
        log_info "Install buildx or use single platform build"
        exit 1
    fi
    
    # Create builder if needed
    if ! docker buildx inspect multiarch >/dev/null 2>&1; then
        log_info "Creating multiarch builder"
        docker buildx create --name multiarch --use
    else
        docker buildx use multiarch
    fi
else
    BUILD_CMD="$BUILD_CMD --platform $PLATFORM"
fi

BUILD_CMD="$BUILD_CMD -f $DOCKERFILE_PATH -t $FULL_IMAGE_NAME $BUILD_CONTEXT"

# Execute build
log_info "Starting build..."
log_debug "Build command: $BUILD_CMD"
echo ""

if eval "$BUILD_CMD"; then
    log_info "Build completed successfully!"
    
    # Show image info
    if [ -z "$MULTI_PLATFORM" ]; then
        echo ""
        log_info "=== Image Information ==="
        docker images "$FULL_IMAGE_NAME" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
    fi
    
    # Push if requested
    if [ -n "$PUSH_IMAGE" ]; then
        echo ""
        log_info "Pushing image to registry..."
        if [ -n "$MULTI_PLATFORM" ]; then
            # For multi-platform, we need to rebuild with --push
            BUILD_CMD="$BUILD_CMD --push"
            if eval "$BUILD_CMD"; then
                log_info "Image pushed successfully!"
            else
                log_error "Failed to push image"
                exit 1
            fi
        else
            if docker push "$FULL_IMAGE_NAME"; then
                log_info "Image pushed successfully!"
            else
                log_error "Failed to push image"
                exit 1
            fi
        fi
    fi
    
    echo ""
    log_info "=== Usage ==="
    log_info "Run container:"
    log_info "  docker run -p 8188:8188 -p 18188:18188 $FULL_IMAGE_NAME"
    echo ""
    log_info "Run with custom environment:"
    log_info "  docker run -p 8188:8188 -p 18188:18188 \\"
    log_info "    -e COMFYUI_SERVER_HOST=0.0.0.0 \\"
    log_info "    -e SERVER_PORT=18188 \\"
    log_info "    $FULL_IMAGE_NAME"
    echo ""
    log_info "Check container logs:"
    log_info "  docker logs -f <container_id>"
    
else
    log_error "Build failed!"
    exit 1
fi 