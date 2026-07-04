# Docker Images

Three Docker images power the CERFAC pipeline:

## 1. cerfac-clinvar
**Purpose**: Extract ClinVar variant data from NCBI  
**Base**: ubuntu:22.04  
**Key tools**: NCBI EDirect, Python (pandas, natsort)  
**Size**: ~257 MB compressed

Runs `get_clinvar_variants.wdl` to query ClinVar via EDirect and parse XML responses.

## 2. cerfac-merge
**Purpose**: Merge functional assay scores with clinical data  
**Base**: ubuntu:22.04  
**Key tools**: Python (pandas, natsort, requests)  
**Size**: ~242 MB compressed

Runs `merge_clinical_functional_data.wdl` to normalize variants and merge datasets via VRS API.

## 3. cerfac-gnomad
**Purpose**: Query population variant frequencies  
**Base**: hailgenetics/hail:0.2.131-py3.11  
**Key tools**: Hail, gnomad package, Python  
**Size**: ~1.28 GB compressed

Runs `get_gnomad_vars.wdl` to retrieve allele frequencies from gnomAD.

## Building

```bash
docker build -t cerfac-clinvar docker/clinvar/
docker build -t cerfac-merge docker/merge_clinical_data/
docker build -t cerfac-gnomad workflows/get_gnomad_variants/docker/
```

## Testing

```bash
docker run --rm cerfac-clinvar esearch -help
docker run --rm cerfac-merge python3 -c "import requests; print('OK')"
docker run --rm cerfac-gnomad python3 -c "import hail; print('OK')"
```

Or use the automated test harness: `./test_harness.sh`

## Notes

- ClinVar and Merge images are 95% identical; consolidation possible in future
- gnomAD image is large due to Hail framework
- EDirect downloads from NCBI at build time (~1-2 minutes)
- All images assume docker user created (though workflows run as root)
