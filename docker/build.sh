#!/bin/bash

# Multi-platform Docker build script for CERFAC images
# Supports building for both ARM64 and AMD64 architectures

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Default to current platform
PLATFORMS="${1:-linux/$(uname -m | sed 's/aarch64/arm64/')}"
PUSH="${2:-false}"  # Set to "push" to push to registry

log_info() {
    echo "ℹ️  $1"
}

log_success() {
    echo "✅ $1"
}

log_error() {
    echo "❌ $1"
}

print_usage() {
    echo "Usage: ./docker/build.sh [PLATFORMS] [ACTION]"
    echo ""
    echo "PLATFORMS (default: current platform):"
    echo "  linux/amd64        - Build for AMD64 (production/Terra)"
    echo "  linux/arm64        - Build for ARM64 (Apple Silicon, ARM servers)"
    echo "  linux/amd64,linux/arm64  - Build for both"
    echo ""
    echo "ACTION (default: load):"
    echo "  load               - Build and load to local Docker (current platform only)"
    echo "  build              - Build multi-platform (doesn't load to Docker)"
    echo "  push               - Build and push to registry (requires registry config)"
    echo ""
    echo "Examples:"
    echo "  ./docker/build.sh                           # Build for current platform, load to Docker"
    echo "  ./docker/build.sh linux/amd64               # Build AMD64 only, load to Docker"
    echo "  ./docker/build.sh linux/amd64,linux/arm64 build  # Build both, don't load"
    echo "  ./docker/build.sh linux/amd64,linux/arm64 push   # Build both and push to registry"
}

# Check if buildx is available
check_buildx() {
    if ! docker buildx version &>/dev/null; then
        log_error "Docker buildx not available"
        echo "Install with: docker buildx create --use"
        exit 1
    fi
    log_success "Docker buildx available"
}

# Build a single image
build_image() {
    local name=$1
    local dockerfile=$2
    local platforms=$3
    local action=$4
    local tag=$5

    log_info "Building $name for platforms: $platforms"

    case "$action" in
        load)
            # Load to local Docker (only works for single platform)
            if [[ "$platforms" == *","* ]]; then
                log_error "Cannot load multiple platforms at once. Use 'build' action instead."
                return 1
            fi
            docker buildx build \
                --platform "$platforms" \
                --load \
                -t "$tag" \
                -f "$dockerfile" \
                "$REPO_ROOT"
            log_success "Loaded $tag ($platforms)"
            ;;
        build)
            # Build multi-platform but don't load
            docker buildx build \
                --platform "$platforms" \
                -t "$tag" \
                -f "$dockerfile" \
                "$REPO_ROOT"
            log_success "Built $tag ($platforms)"
            ;;
        push)
            # Build and push to registry
            docker buildx build \
                --platform "$platforms" \
                --push \
                -t "$tag" \
                -f "$dockerfile" \
                "$REPO_ROOT"
            log_success "Pushed $tag ($platforms)"
            ;;
        *)
            log_error "Unknown action: $action"
            return 1
            ;;
    esac
}

# Main
main() {
    echo "CERFAC Multi-Platform Docker Builder"
    echo "====================================="
    echo ""

    if [[ "$PLATFORMS" == "help" || "$PLATFORMS" == "-h" || "$PLATFORMS" == "--help" ]]; then
        print_usage
        exit 0
    fi

    # Determine action
    case "$PUSH" in
        push)
            ACTION="push"
            ;;
        build)
            ACTION="build"
            ;;
        *)
            ACTION="load"
            ;;
    esac

    # Check requirements
    check_buildx

    # Current platform for reference
    current_platform="linux/$(uname -m | sed 's/x86_64/amd64/; s/aarch64/arm64/')"
    echo "Current system platform: $current_platform"
    echo "Build target platforms: $PLATFORMS"
    echo "Action: $ACTION"
    echo ""

    # Build images
    build_image "cerfac-clinvar" \
        "$SCRIPT_DIR/clinvar/Dockerfile" \
        "$PLATFORMS" \
        "$ACTION" \
        "cerfac-clinvar:latest"

    build_image "cerfac-merge" \
        "$SCRIPT_DIR/merge_clinical_data/Dockerfile" \
        "$PLATFORMS" \
        "$ACTION" \
        "cerfac-merge:latest"

    build_image "cerfac-gnomad" \
        "$REPO_ROOT/workflows/get_gnomad_variants/docker/Dockerfile" \
        "$PLATFORMS" \
        "$ACTION" \
        "cerfac-gnomad:latest"

    echo ""
    log_success "All images built successfully!"

    if [[ "$ACTION" == "load" ]]; then
        echo ""
        echo "Loaded images:"
        docker images | grep -E "cerfac-|REPOSITORY"
    fi
}

main "$@"
