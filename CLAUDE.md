# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CERFAC (Cloud-based, Evidence-based, Rigorous Functional Assay Calibration) is a bioinformatics pipeline for validating functional assay predictions against clinical observational data. It uses WDL workflows to:

1. Extract variant data from ClinVar (clinical database)
2. Retrieve gnomAD population variant frequencies
3. Merge calibration data with user-provided functional assay scores and clinical observations
4. Perform statistical calibration analysis (odds ratio calculations) via Jupyter notebook

The project is designed for deployment on Terra (Broad Institute) but can also run standalone using Cromwell.

## Architecture

### Workflow Structure

The main execution flows through three sequential WDL workflows:

- **workflows/combined_gnomad_clinvar/get_clinvar_variants.wdl**: Queries NCBI ClinVar via Entrez Direct (EDirect). Creates 5 parallel extraction tasks using bash/awk to parse XML, then merges results. Output: CSV with one row per submitter per variant.

- **workflows/combined_gnomad_clinvar/get_gnomad_vars.wdl**: Queries gnomAD using the Hail Python package. Memory allocation is dynamic based on gene length (15 GB base + 30 GB for genes >1M bp, +45 GB for >2M bp). Merges gnomAD output with ClinVar results.

- **workflows/combined_gnomad_clinvar/merge_clinical_functional_data.wdl**: Normalizes variants across files using VRS IDs (via an external API) to handle nomenclature variations. Accepts TSV/CSV/TXT input with HGVS or gnomAD VCF format variants. **Critical: variant ID must be first column.**

### Additional Components

- **workflows/combined_gnomad_clinvar/merge_clinvar_variants.py**: Python script that merges multiple ClinVar extraction outputs
- **notebooks/notebooks_OR_Calculations.ipynb**: R-based Jupyter notebook for statistical analysis and threshold calibration
- **.dockstore.yml**: Dockstore registry configuration (version 1.3.1) for workflow publication

### Docker & Cromwell

- **cromwell.conf**: Configures Cromwell backend (default: Local). Uses Docker containers for task isolation.
- **docker/**: Container images referenced in workflows (e.g., `allisoncheney/cerfac_terra:clinvar`)
- Runtime attributes in tasks specify memory, CPU, disk, and Docker image per task

## Common Development Tasks

### Running a Single Workflow Locally with Cromwell

```bash
java -Dconfig.file=workflows/combined_gnomad_clinvar/cromwell.conf \
     -jar /path/to/cromwell.jar run \
     workflows/combined_gnomad_clinvar/get_clinvar_variants.wdl \
     --inputs workflows/test/get_clinvar_variants.brca1.input.json
```

Test inputs are in `workflows/test/` (e.g., `get_clinvar_variants.brca1.input.json`)

### Testing a Workflow Syntax

Use cromwell's `validate` command to check WDL syntax before running:

```bash
java -jar /path/to/cromwell.jar validate workflows/combined_gnomad_clinvar/get_clinvar_variants.wdl
```

### Modifying Data Processing

- **ClinVar extraction**: Edit tasks in `get_clinvar_variants.wdl` (e.g., change EDirect queries or XML parsing logic)
- **gnomAD filtering**: Edit `get_gnomad_vars.wdl` (Hail/Python code embedded in task blocks)
- **Variant merging logic**: Edit `merge_clinical_functional_data.wdl` or `merge_clinvar_variants.py`

### Updating Example Data

Example clinical and functional assay data files are in `example_data/`:
- `Case_control_data.tsv` — clinical case/control observations
- `Uncalibrated_functional_assay.tsv` — functional assay scores

These are referenced in the step-by-step documentation and used for user testing on Terra.

## Variant Nomenclature & Data Requirements

**Input Format Requirements** (critical for merge workflow):

1. Variant ID must be in **first column**
2. Accepted formats:
   - **HGVS DNA coding** (cDNA): `c.884G>A`, `c.897+9T>C`, `c.919_920del` — **must use MANE Select transcript** (no transcript ID or gene name prefix)
   - **gnomAD VCF**: `chrom-pos-ref-alt` (dashes as separators, not colons/underscores)
   - **HGVS genomic**: `g.` format (less common)

**Known Parsing Issues** (variants that will skip, not abort):

- HGVS with `inv` (inversions) — API doesn't support
- HGVS with bases after `dup`/`del` (e.g., `c.100_102dupAAA`) — not supported
- Non-ACTG bases in variant
- Coding variants in introns/upstream (with `+` or `-`) — intronic coding not supported, but VCF format is OK
- HGVS with asterisks

**Abort Errors** (halt entire workflow):

- Missing first line of column names
- HGVS without accession (gene name alone is insufficient)
- Missing `:` separator between accession and `g.` or `c.` in first variant

## Testing

Test input files are in `workflows/test/`:
- `get_gnomad_variants.brca1.input.json` — sample BRCA1 test inputs
- `get_gnomad_variants.pten.input.json` — sample PTEN test inputs

**Note**: ClinVar test inputs need to be created or obtained from Terra workspace.

Run tests against known reference genes (BRCA1 is well-characterized; PTEN is smaller).

## Docker Images & Setup

### Quick Reference

Three Docker images power the pipeline:

1. **cerfac-clinvar** (`docker/clinvar/Dockerfile`): NCBI EDirect + Python (pandas, natsort)
   - Used for: ClinVar variant extraction via XML parsing
   - Size: ~257 MB

2. **cerfac-merge** (`docker/merge_clinical_data/Dockerfile`): Python with requests library
   - Used for: Variant normalization API calls + data merging
   - Size: ~242 MB

3. **cerfac-gnomad** (`workflows/get_gnomad_variants/docker/Dockerfile`): Hail + gnomad package
   - Used for: Population frequency queries
   - Size: ~2+ GB (includes Hail JVM)

**See [docker/README.md](docker/README.md) for detailed image information.**

### Building Images Locally

**Multi-platform builder** (recommended):
```bash
# Build for current platform
./docker/build.sh

# Build for specific platform
./docker/build.sh linux/amd64          # AMD64 (production/Terra)
./docker/build.sh linux/arm64          # ARM64 (Apple Silicon, ARM servers)
./docker/build.sh linux/amd64,linux/arm64 build  # Both platforms
```

Supports building for AMD64 (production workflows) and ARM64 (local development). Uses Docker buildx for efficient multi-platform builds.

**Manual builds** (single platform):
```bash
docker build -t cerfac-clinvar:latest docker/clinvar/
docker build -t cerfac-merge:latest docker/merge_clinical_data/
docker build -t cerfac-gnomad:latest workflows/get_gnomad_variants/docker/
```

### Testing Docker Installation

```bash
# Quick validation
docker run --rm cerfac-clinvar:latest esearch -help
docker run --rm cerfac-merge:latest python3 -c "import requests; print(requests.__version__)"
docker run --rm cerfac-gnomad:latest python3 -c "import hail; print(hail.__version__)"
```

## Cromwell Configuration & Testing

### Local Cromwell Setup

A pre-downloaded Cromwell JAR is included: `tools/cromwell-86.jar` (241 MB)

**Prerequisites**:
- Java Runtime Environment (JRE) - `brew install java` on macOS
- Docker daemon running
- `cromwell.conf` in `workflows/combined_gnomad_clinvar/`

### WDL Validation

```bash
java -jar tools/cromwell-86.jar validate workflows/combined_gnomad_clinvar/get_clinvar_variants.wdl
```

### Running Workflows Locally

```bash
java -Dconfig.file=workflows/combined_gnomad_clinvar/cromwell.conf \
     -jar tools/cromwell-86.jar run \
     workflows/combined_gnomad_clinvar/get_clinvar_variants.wdl \
     --inputs workflows/test/get_clinvar_variants.brca1.input.json
```

**See [CROMWELL_SETUP.md](CROMWELL_SETUP.md) for detailed configuration and troubleshooting.**

## Key External Dependencies

- **NCBI EDirect**: Command-line E-utilities interface (bash commands in `get_clinvar_variants.wdl`)
- **Hail**: Python package for gnomAD queries
- **VRS/Variation ID API**: Used in `merge_clinical_functional_data.wdl` to normalize variant nomenclature
- **Terra workspace** (production): Handles file management, data tables, workflow execution, cost tracking

## Cleanup & Infrastructure

### Files Added

- **docker/build.sh** - Multi-platform Docker builder for AMD64 and ARM64
- **docker/README.md** - Docker image reference and documentation
- **CROMWELL_SETUP.md** - Cromwell installation, configuration, and troubleshooting guide
- **test_harness.sh** - Automated testing script for Docker images and WDL validation
- **tools/cromwell-86.jar** - Cromwell workflow engine (241 MB, not committed to git)

### Files Deleted

- `test_wdl/` - Entire directory (old development test files, no longer part of pipeline)
- `old.dockstore.yml` - Superseded by current `.dockstore.yml` (v1.2 → v1.3.1)

### Files Updated

- `.gitignore` - Added `.DS_Store` (macOS) and `tools/` (build artifacts)
- `README.md` - Expanded with project overview and quick start guide
- `docker/clinvar/Dockerfile` - Fixed ADD path for multi-platform builds

### Documentation Policy

Only infrastructure and reference documentation is committed to the repository. Session-specific communication documents (e.g., FINAL_STATUS.md, NEXT_STEPS.md) are not committed.

## Notes for Modifications

- **Memory tuning**: If gnomAD queries fail with OOM, check the dynamic memory calculation in `get_gnomad_vars.wdl`. Adjust the formula if working with unexpectedly large genes.
- **ClinVar updates**: EDirect queries return latest ClinVar data; output format may change if NCBI modifies their XML schema.
- **VRS API changes**: If variant normalization fails, the external VRS API may have been updated; check `merge_clinical_functional_data.wdl` for API version or endpoint.
- **Docker image updates**: Workflows reference specific Docker images. Rebuild and push if dependencies change. Use `test_harness.sh` to verify locally.
- **Cromwell version**: cromwell.conf is tuned for specific Cromwell versions; compatibility issues may arise with major version upgrades.
- **EDirect installation**: ClinVar Dockerfile downloads EDirect at build time; requires internet access and may be slow.

## Documentation Files

- **CERFAC_documentation.md** — User-facing step-by-step guide for Terra (clone workspace, upload data, run workflows, interpret results)
- **README.md** — Project title and link to documentation
- **.dockstore.yml** — Workflow metadata for Dockstore registry (authors, test parameter files, version)

## Important Constraints & Quirks

- Workflows assume **GRCh38** reference genome (hardcoded in ClinVar query)
- MANE Select transcript is expected; transcripts vary by gene
- gnomAD query time scales with gene length; very large genes (>2M bp) may take 20+ minutes
- ClinVar extraction can return multiple rows per variant (one per submitter); downstream merging deduplicates
- Case/control counts and disease frequency are user inputs to the R notebook; units matter for OR calculations
