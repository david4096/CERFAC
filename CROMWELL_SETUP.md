# Cromwell Setup and Testing Guide

## Installation

A pre-downloaded Cromwell JAR (version 86) is included in this repository:
- **Location**: `tools/cromwell-86.jar`
- **Size**: ~241 MB
- **SHA256**: f9581657e0484c90b5ead0f699d8d791f94e3cabe87d8cb0c5bfb21d1fdb6592

### Prerequisites

1. **Java Runtime Environment (JRE)** - Required to run Cromwell
   ```bash
   # Check if Java is installed
   java -version
   
   # macOS (using Homebrew)
   brew install java
   
   # Linux (Ubuntu/Debian)
   sudo apt-get install default-jre
   
   # Or install OpenJDK
   brew install openjdk
   ```

2. **Docker** - Required for containerized workflow execution
   ```bash
   # Check if Docker is installed
   docker --version
   ```

## Configuration

The default Cromwell configuration is in `workflows/combined_gnomad_clinvar/cromwell.conf`:

```conf
backend {
  default = Local
  providers {
    Local {
      actor-factory = "cromwell.backend.impl.sfs.config.ConfigBackendLifecycleActorFactory"
      config {
        run-in-background = true
        submit-docker = """
        docker run \
          --cidfile ${docker_cid} \
          -i \
          --memory=7g \
          --cpus=2 \
          --entrypoint ${job_shell} \
          -v ${cwd}:${docker_cwd} \
          ${docker} ${docker_script}
        """
      }
    }
  }
}
```

**Configuration Details**:
- **Backend**: Local (runs on the machine, not cloud)
- **Memory Default**: 7 GB per task
- **CPU Default**: 2 cores per task
- **Docker**: Enabled with volume mounts

## Running Workflows

### Syntax Validation

Validate a WDL file without running it:

```bash
java -jar tools/cromwell-86.jar validate workflows/combined_gnomad_clinvar/get_clinvar_variants.wdl
```

### Running a Workflow

Execute a workflow with input JSON:

```bash
java -Dconfig.file=workflows/combined_gnomad_clinvar/cromwell.conf \
     -jar tools/cromwell-86.jar run \
     workflows/combined_gnomad_clinvar/get_clinvar_variants.wdl \
     --inputs workflows/test/get_clinvar_variants.brca1.input.json
```

### Available Test Inputs

Located in `workflows/test/`:
- `get_gnomad_variants.brca1.input.json` - gnomAD query for BRCA1 gene
- `get_gnomad_variants.pten.input.json` - gnomAD query for PTEN gene

## Common Commands

```bash
# Validate WDL syntax
java -jar tools/cromwell-86.jar validate workflows/combined_gnomad_clinvar/get_clinvar_variants.wdl

# Run workflow (assuming inputs are defined)
java -Dconfig.file=workflows/combined_gnomad_clinvar/cromwell.conf \
     -jar tools/cromwell-86.jar run workflows/combined_gnomad_clinvar/get_clinvar_variants.wdl \
     --inputs <input-file.json>

# List version
java -jar tools/cromwell-86.jar --version

# Get help
java -jar tools/cromwell-86.jar --help
```

## Troubleshooting

### Java Not Found
```
The operation couldn't be completed. Unable to locate a Java Runtime.
```
**Solution**: Install JRE/JDK (see Prerequisites above)

### Docker Not Available
```
ERROR: error creating mount: mkdir /var/lib/docker/volumes/...
```
**Solution**: Ensure Docker daemon is running and user has permissions

### OOM (Out of Memory)
Edit `cromwell.conf` to increase `--memory` in the `submit-docker` section.

### Task Timeout
Add timeout configuration to the WDL task:
```wdl
runtime {
  memory: "8 GB"
  cpu: 2
  docker: "image:tag"
  maxRetries: 3
  timeout: 3600  # seconds
}
```

## Output

Cromwell creates a `cromwell-executions/` directory containing:
- Logs: `workflow.log`, task logs
- Outputs: Task and workflow outputs
- Metadata: `metadata.json` with full execution details

## Useful Links

- [Cromwell Documentation](https://cromwell.readthedocs.io/)
- [WDL Spec](https://github.com/openwdl/wdl)
- [Cromwell GitHub Releases](https://github.com/broadinstitute/cromwell/releases)

