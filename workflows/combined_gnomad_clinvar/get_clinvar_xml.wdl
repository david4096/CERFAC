version 1.0

workflow get_clinvar_xml {

    meta {
        author: "Allison Cheney"
        email: "archeney@ucsc.edu"
        description: "Download ClinVar XML data for a specified gene"
    }

    parameter_meta {
        GENE_NAME: "Name of relevant gene"
    }

    input {
        String GENE_NAME
    }

    call get_clinvar_variants_file {
        input: GENE_NAME=GENE_NAME
    }

    output {
        File output_clinvar_xml = get_clinvar_variants_file.basicxml
    }
}


task get_clinvar_variants_file {
    input {
        String GENE_NAME
        Int memSizeGB = 16
        Int threadCount = 2
        Int diskSizeGB = 20
    }

    command <<<
        set -eux -o pipefail

        # Query ClinVar and save results, handling large datasets
        esearch -db clinvar -query "~{GENE_NAME}[GENE] AND homo sapiens [ORGN] AND (varlen 49 or less[FILTER]) NOT (near gene upstream[PROP]) NOT (near gene downstream[PROP])" | \
        efetch -format variationid -stop 10000 > basic.xml || {
            # If first attempt fails, try without the stop limit
            esearch -db clinvar -query "~{GENE_NAME}[GENE] AND homo sapiens [ORGN] AND (varlen 49 or less[FILTER]) NOT (near gene upstream[PROP]) NOT (near gene downstream[PROP])" | \
            efetch -format variationid > basic.xml
        }

        # Verify file was created
        if [ ! -s basic.xml ]; then
            echo "ERROR: Failed to download ClinVar data" >&2
            exit 1
        fi
    >>>

    output {
        File basicxml  = "basic.xml"
    }

    runtime {
        memory: memSizeGB + " GB"
        cpu: threadCount
        disks: "local-disk " + diskSizeGB + " SSD"
        docker: "allisoncheney/cerfac_terra:clinvar"
        docker_memory_gb: 12
        docker_cpu: 4
        maxRetries: 1
        preemptible: 1
    }
}
