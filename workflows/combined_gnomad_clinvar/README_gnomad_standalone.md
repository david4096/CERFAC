# gnomAD Variants Workflows

This directory contains two versions of the gnomAD variant extraction workflow:

## `get_gnomad_vars.wdl` - Full Pipeline with ClinVar Merge

**Purpose**: Extract gnomAD variants and merge with ClinVar data for comprehensive variant annotation.

**Inputs**:
- `GENE_NAME` - Gene to query (e.g., "BRCA1")
- `clinvar_var` - ClinVar variants CSV file (from `get_clinvar_variants.wdl`)

**Outputs**:
- `{GENE_NAME}_calibration_variants.csv` - Combined gnomAD + ClinVar data
- Variant counts for gnomAD and combined datasets
- Gene location information

**Use Case**: Creating calibration datasets that combine population genetics (gnomAD) with clinical significance (ClinVar) for variant interpretation pipelines.

**Workflow Steps**:
1. Extract gene location from ClinVar
2. Query gnomAD for variants in gene region
3. **Merge with ClinVar data**
4. Output combined dataset

---

## `get_gnomad_vars_standalone.wdl` - gnomAD Only (No ClinVar Merge)

**Purpose**: Extract gnomAD variants without requiring ClinVar data.

**Inputs**:
- `GENE_NAME` - Gene to query (e.g., "PTEN")

**Outputs**:
- `{GENE_NAME}_gnomad_variants_MANE.csv` - gnomAD variants only
- `gnomad_variants_count` - Number of unique variants found
- Gene location information (chr, start, end, length)

**Use Case**: When you only need population frequency data from gnomAD, or when running gnomAD extraction independently of ClinVar.

**Workflow Steps**:
1. Extract gene location from ClinVar (for coordinates only)
2. Query gnomAD for variants in gene region
3. Output gnomAD dataset

---

## Key Differences

| Feature | Full Pipeline | Standalone |
|---------|--------------|------------|
| ClinVar input required | ✅ Yes | ❌ No |
| ClinVar merge task | ✅ Included | ❌ Removed |
| Output columns | Combined (gnomAD + ClinVar) | gnomAD only |
| Variant source labels | "gnomAD and ClinVar", "ClinVar only", "gnomAD only" | "gnomAD" |
| Output file naming | `{GENE}_calibration_variants.csv` | `{GENE}_gnomad_variants_MANE.csv` |
| Use case | Variant interpretation/ML training | Population frequency analysis |

---

## Common Features (Both Workflows)

Both workflows share the same gnomAD extraction logic:

### Data Sources
- **gnomAD v4 Exomes** - Whole exome sequencing data
- **gnomAD v4 Genomes** - Whole genome sequencing data

### Filters Applied
- ✅ Canonical transcripts only
- ✅ MANE Select transcripts (NM_*)
- ✅ Target gene only
- ✅ Coding variants (missense, nonsense, frameshift)
- ❌ UTR variants excluded
- ❌ Intronic variants excluded
- ❌ Upstream variants excluded

### Population Frequencies
Both workflows extract allele frequencies for 9 ancestry groups:
- AFR (African/African American)
- AMR (Latino/Admixed American)
- EAS (East Asian)
- NFE (Non-Finnish European)
- SAS (South Asian)
- MID (Middle Eastern)
- FIN (Finnish)
- ASJ (Ashkenazi Jewish)
- RMI (Remaining)

### Annotations Included
- VEP (Variant Effect Predictor) annotations
- HGVS nomenclature (cDNA and protein)
- VRS (Variant Representation Specification) identifiers
- Functional predictions (LoF, SpliceAI)
- Transcript information (MANE Select, exon/intron)

---

## Usage Examples

### Standalone Workflow (gnomAD only)

```bash
# Create input JSON
cat > pten.input.json <<EOF
{
  "get_gnomad_variants_standalone.GENE_NAME": "PTEN"
}
EOF

# Run with Cromwell
java -jar cromwell.jar run get_gnomad_vars_standalone.wdl -i pten.input.json

# Run on Terra
# 1. Upload get_gnomad_vars_standalone.wdl to workspace
# 2. Create workflow with GENE_NAME input
# 3. Launch analysis
```

### Full Pipeline (with ClinVar merge)

```bash
# First, run ClinVar workflow
java -jar cromwell.jar run get_clinvar_variants.wdl -i clinvar.input.json

# Then run gnomAD with merge
cat > gnomad.input.json <<EOF
{
  "get_gnomad_variants.GENE_NAME": "PTEN",
  "get_gnomad_variants.clinvar_var": "path/to/clinvar_variants.csv"
}
EOF

java -jar cromwell.jar run get_gnomad_vars.wdl -i gnomad.input.json
```

---

## Resource Requirements

Both workflows have the same resource needs:

**Small genes** (< 100 kb, like PTEN):
- Memory: 15 GB
- Disk: 35 GB
- Runtime: ~10-20 minutes

**Medium genes** (100 kb - 1 Mb):
- Memory: 15 GB
- Disk: 35 GB
- Runtime: ~15-30 minutes

**Large genes** (1-2 Mbp):
- Memory: 45 GB
- Disk: 65 GB
- Runtime: ~30-60 minutes

**Very large genes** (> 2 Mbp):
- Memory: 90 GB
- Disk: 110 GB
- Runtime: 1-2 hours

---

## Output File Structure

### Standalone Output (`{GENE}_gnomad_variants_MANE.csv`)

All columns have `_gnomad` suffix. Key columns include:

- `CERFAC_variant_id_VCF_gnomad` - Variant ID in VCF format
- `HGVS_cDNA_ID_gnomad` - HGVS cDNA identifier
- `hgvs_pro_gnomad` - HGVS protein change
- `exome_freq_main_adj_*` - Exome frequencies by population
- `genome_freq_adj_*` - Genome frequencies by population
- `variant_effect_gnomad` - Variant consequence
- `txpt_mane_select_gnomad` - MANE Select transcript ID
- `spliceai_ds_max_gnomad` - SpliceAI score
- `set_gnomad` - Data source: "exomes", "genomes", or "both"

### Full Pipeline Output (`{GENE}_calibration_variants.csv`)

Includes all gnomAD columns PLUS ClinVar columns:

- All gnomAD columns (with `_gnomad` suffix)
- All ClinVar columns (with `_clinvar` suffix)
- `variant_source` - Combined source label
- Merged on `VCF_genomic_ID`

---

## When to Use Which Workflow

### Use Standalone (`get_gnomad_vars_standalone.wdl`) when:
- ✅ You only need population frequency data
- ✅ You're analyzing benign/common variants
- ✅ You don't have ClinVar data yet
- ✅ You're running gnomAD extraction separately

### Use Full Pipeline (`get_gnomad_vars.wdl`) when:
- ✅ You need both clinical and population data
- ✅ You're building variant interpretation pipelines
- ✅ You're training ML models for pathogenicity prediction
- ✅ You want to identify variants unique to each database
- ✅ You need comprehensive variant calibration datasets

---

## Technical Notes

1. **Cloud Execution Recommended**: Both workflows download large gnomAD datasets and work best on Terra/Cromwell cloud infrastructure

2. **Hail Framework**: Both use Hail for distributed genomics data processing

3. **MANE Transcripts**: Both filter to MANE Select transcripts for clinical consistency

4. **Dynamic Resources**: Memory and disk scale automatically based on gene size

5. **Docker Images**:
   - `allisoncheney/cerfac_terra:clinvar` - For gene location extraction
   - `allisoncheney/cerfac_terra:gnomad` - For gnomAD data processing (has Hail + gnomAD packages)

---

## Output Column Counts

- **Standalone**: ~100-120 columns (all gnomAD annotations)
- **Full Pipeline**: ~150-200 columns (gnomAD + ClinVar annotations)
