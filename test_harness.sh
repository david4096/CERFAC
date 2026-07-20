#!/bin/bash

# CERFAC Test Harness
# Demonstrates the functionality of each Docker image and workflow component

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$SCRIPT_DIR/docker"
WORKFLOWS_DIR="$SCRIPT_DIR/workflows"
TOOLS_DIR="$SCRIPT_DIR/tools"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_section() {
    echo ""
    echo -e "${YELLOW}=== $1 ===${NC}"
}

# Check prerequisites
check_prerequisites() {
    log_section "Checking Prerequisites"

    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    log_success "Docker is installed ($(docker --version))"

    if ! command -v java &> /dev/null; then
        log_error "Java is not installed (required for Cromwell)"
        echo "  Install with: brew install java"
        exit 1
    fi
    log_success "Java is installed ($(java -version 2>&1 | head -1))"

    if [ ! -f "$TOOLS_DIR/cromwell-86.jar" ]; then
        log_error "Cromwell JAR not found at $TOOLS_DIR/cromwell-86.jar"
        exit 1
    fi
    log_success "Cromwell JAR found"
}

# Build Docker images
build_docker_images() {
    log_section "Building Docker Images"

    # ClinVar image
    log_info "Building ClinVar extraction image..."
    if docker build -t cerfac-clinvar:latest "$DOCKER_DIR/clinvar/" > /tmp/clinvar-build.log 2>&1; then
        log_success "ClinVar image built successfully"
    else
        log_error "Failed to build ClinVar image"
        tail -20 /tmp/clinvar-build.log
        return 1
    fi

    # Merge data image
    log_info "Building merge clinical data image..."
    if docker build -t cerfac-merge:latest "$DOCKER_DIR/merge_clinical_data/" > /tmp/merge-build.log 2>&1; then
        log_success "Merge image built successfully"
    else
        log_error "Failed to build merge image"
        tail -20 /tmp/merge-build.log
        return 1
    fi

    # gnomAD image
    log_info "Building gnomAD query image..."
    if docker build -t cerfac-gnomad:latest "$WORKFLOWS_DIR/get_gnomad_variants/docker/" > /tmp/gnomad-build.log 2>&1; then
        log_success "gnomAD image built successfully"
    else
        log_error "Failed to build gnomAD image"
        tail -20 /tmp/gnomad-build.log
        return 1
    fi
}

# Test ClinVar image
test_clinvar_image() {
    log_section "Testing ClinVar Image"

    log_info "Testing EDirect availability..."
    if docker run --rm cerfac-clinvar:latest esearch -help &> /dev/null; then
        log_success "EDirect is available"
    else
        log_error "EDirect not available"
        return 1
    fi

    log_info "Testing Python packages..."
    if docker run --rm cerfac-clinvar:latest python3 -c "import pandas; import natsort; print(f'pandas {pandas.__version__}, natsort {natsort.__version__}')" &> /tmp/clinvar-python.log; then
        log_success "Python packages available: $(cat /tmp/clinvar-python.log)"
    else
        log_error "Python packages not available"
        return 1
    fi

    log_info "Testing cv_merge_script.py..."
    if docker run --rm cerfac-clinvar:latest python3 -c "import sys; sys.path.insert(0, '/home'); exec(open('/home/cv_merge_script.py').read()); print('Script loaded')" &> /tmp/clinvar-script.log 2>&1; then
        log_success "cv_merge_script.py is available"
    else
        log_error "cv_merge_script.py not accessible"
        cat /tmp/clinvar-script.log | head -5
    fi
}

# Test Merge image
test_merge_image() {
    log_section "Testing Merge Clinical Data Image"

    log_info "Testing requests library..."
    if docker run --rm cerfac-merge:latest python3 -c "import requests; print(f'requests {requests.__version__}')" &> /tmp/merge-requests.log; then
        log_success "Requests available: $(cat /tmp/merge-requests.log)"
    else
        log_error "Requests not available"
        return 1
    fi

    log_info "Testing Python packages..."
    if docker run --rm cerfac-merge:latest python3 -c "import pandas, natsort; print('pandas and natsort available')" &> /dev/null; then
        log_success "All Python packages available"
    else
        log_error "Python packages not available"
        return 1
    fi
}

# Test gnomAD image
test_gnomad_image() {
    log_section "Testing gnomAD Image"

    log_info "Testing Hail availability..."
    if docker run --rm cerfac-gnomad:latest python3 -c "import hail; print(f'Hail {hail.__version__}')" &> /tmp/gnomad-hail.log; then
        log_success "Hail available: $(cat /tmp/gnomad-hail.log)"
    else
        log_error "Hail not available"
        cat /tmp/gnomad-hail.log
        return 1
    fi

    log_info "Testing gnomad package..."
    if docker run --rm cerfac-gnomad:latest python3 -c "import gnomad; print('gnomad package available')" &> /tmp/gnomad-pkg.log 2>&1; then
        log_success "gnomad package available"
    else
        log_error "gnomad package not available"
        cat /tmp/gnomad-pkg.log | head -5
    fi

    log_info "Testing pandas..."
    if docker run --rm cerfac-gnomad:latest python3 -c "import pandas; print(f'pandas {pandas.__version__}')" &> /tmp/gnomad-pandas.log; then
        log_success "pandas available: $(cat /tmp/gnomad-pandas.log)"
    else
        log_error "pandas not available"
        return 1
    fi
}

# Test Cromwell validation
test_cromwell_validation() {
    log_section "Testing Cromwell WDL Validation"

    # Test validating WDL files
    local wdl_files=(
        "$WORKFLOWS_DIR/combined_gnomad_clinvar/get_clinvar_variants.wdl"
        "$WORKFLOWS_DIR/combined_gnomad_clinvar/get_gnomad_vars.wdl"
        "$WORKFLOWS_DIR/combined_gnomad_clinvar/merge_clinical_functional_data.wdl"
        "$WORKFLOWS_DIR/get_gnomad_variants/get_gnomad_variants.wdl"
    )

    for wdl_file in "${wdl_files[@]}"; do
        if [ ! -f "$wdl_file" ]; then
            log_error "WDL file not found: $wdl_file"
            continue
        fi

        local filename=$(basename "$wdl_file")
        log_info "Validating $filename..."
        if java -jar "$TOOLS_DIR/cromwell-86.jar" validate "$wdl_file" > /tmp/cromwell-validate.log 2>&1; then
            log_success "$filename is valid"
        else
            log_error "$filename validation failed"
            cat /tmp/cromwell-validate.log | head -10
        fi
    done
}

# Summary function
print_summary() {
    log_section "Test Summary"

    log_info "Verifying built images..."
    docker images | grep cerfac || log_error "No cerfac images found"

    log_success "All tests completed!"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "  1. Review DOCKER_ANALYSIS.md for detailed Docker image information"
    echo "  2. Review CROMWELL_SETUP.md for Cromwell configuration and usage"
    echo "  3. Run workflows with: java -jar tools/cromwell-86.jar run <workflow.wdl> --inputs <inputs.json>"
}

# Main execution
main() {
    log_info "CERFAC Test Harness Starting"

    check_prerequisites || exit 1

    if build_docker_images; then
        test_clinvar_image
        test_merge_image
        test_gnomad_image
        test_cromwell_validation
        print_summary
    else
        log_error "Docker image build failed"
        exit 1
    fi
}

main "$@"
