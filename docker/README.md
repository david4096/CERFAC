# CERFAC Docker Images

## Quick Build

Build for your current platform:
```bash
./docker/build.sh
```

This builds and loads `cerfac-clinvar`, `cerfac-merge`, and `cerfac-gnomad` images to your local Docker.

## Multi-Platform Building

Build for specific platforms:

```bash
# Build for AMD64 only (production)
./docker/build.sh linux/amd64

# Build for ARM64 only (Apple Silicon, ARM servers)
./docker/build.sh linux/arm64

# Build for both platforms
./docker/build.sh linux/amd64,linux/arm64 build

# Build both and push to registry
./docker/build.sh linux/amd64,linux/arm64 push
```

## Architecture Notes

- **AMD64** (`linux/amd64`): Production/Terra environment. All WDL workflows use this.
- **ARM64** (`linux/arm64`): Local testing on Apple Silicon and ARM-based systems.

The build script automatically detects your system:
- Mac M1/M2/M3: `linux/arm64`
- Intel Mac: `linux/amd64`
- Linux x86_64: `linux/amd64`
- Linux ARM: `linux/arm64`

## Using the Build Script

### Load to Local Docker (Single Platform)
```bash
./docker/build.sh linux/amd64 load
```
Builds and loads AMD64 images so you can run them immediately.

### Multi-Platform Build (No Load)
```bash
./docker/build.sh linux/amd64,linux/arm64 build
```
Builds for both platforms but doesn't load to local Docker (image is in buildx cache).

### Push to Registry
```bash
./docker/build.sh linux/amd64,linux/arm64 push
```
Builds for both platforms and pushes to Docker Hub or private registry.

Requires Docker image names to include registry:
```bash
# Modify image tags in the script or use environment variables
```

## Prerequisites

Docker buildx must be available:
```bash
docker buildx version
```

If not installed:
```bash
docker buildx create --use
```

## Images

See [DOCKER_ANALYSIS.md](DOCKER_ANALYSIS.md) for details on each image.

## Testing

Test locally built images:
```bash
docker run --rm cerfac-clinvar esearch -help
docker run --rm cerfac-merge python3 -c "import requests"
docker run --rm cerfac-gnomad python3 -c "import hail"
```

Or use the automated test harness:
```bash
../test_harness.sh
```
