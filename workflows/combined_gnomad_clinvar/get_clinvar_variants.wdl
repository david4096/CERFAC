version 1.0

workflow get_clinvar_variants {

    meta {
        author: "Allison Cheney"
        email: "archeney@ucsc.edu"
        description: "Extract variants for a specified gene"
    }

    parameter_meta {
        GENE_NAME: "Name of relevant gene"
    }
    input {
        String GENE_NAME        
    }
    #The order in which the workflow block and task definitions are arranged in the script does not matter. 
    #Nor does the order of the call statements matter, as we'll see further on.

    call  get_clinvar_variants_file{
        input: GENE_NAME=GENE_NAME
    }
    call extract_clinvar_variants_traitmap{
        input: 
            GENE_NAME=GENE_NAME,
            basicxml=get_clinvar_variants_file.basicxml
    }
    call extract_clinvar_variants_traitset{
        input: 
            GENE_NAME=GENE_NAME,
            basicxml=get_clinvar_variants_file.basicxml
    }
    call extract_clinvar_variants_basic{
        input: 
            GENE_NAME=GENE_NAME,
            basicxml=get_clinvar_variants_file.basicxml
    }
    call merge_clinvar_variants{
        input: 
            basiccv=extract_clinvar_variants_basic.basiccv, 
            traitset=extract_clinvar_variants_traitset.traitset, 
            traitmap=extract_clinvar_variants_traitmap.traitmap
    }

    output{
        File output_clinvar_variants = merge_clinvar_variants.clinvar_var
        String output_clinvar_variants_count = merge_clinvar_variants.clinvar_variants_count
    }
}



task get_clinvar_variants_file {
    input {
        String GENE_NAME
        Int memSizeGB = 10
        Int threadCount = 1
        Int diskSizeGB = 10
    }

    command <<<
        set -eux -o pipefail

        esearch -db clinvar -query "~{GENE_NAME}[GENE] AND homo sapiens [ORGN] AND (varlen 49 or less[FILTER]) NOT (near gene upstream[PROP]) NOT (near gene downstream[PROP])" |
        efetch -format variationid > basic.xml
    >>>

    output {
        File basicxml  = "basic.xml"
    }

    runtime {
        memory: memSizeGB + " GB"
        cpu: threadCount
        disks: "local-disk " + diskSizeGB + " SSD"
        docker: "allisoncheney/cerfac_terra:clinvar"
        maxRetries: 1
        preemptible: 1
    }
}

task extract_clinvar_variants_traitmap {
    input {
        String GENE_NAME
        File basicxml  
        Int memSizeGB = 10
        Int threadCount = 1
        Int diskSizeGB = 5*round(size(basicxml, "GB")) + 2

    }

    command <<<
        set -eux -o pipefail

        cat  ~{basicxml} |
        xtract -pattern VariationArchive -def 'NA' -KEYVCV VariationArchive@Accession \
                -group TraitMapping -deq '\n' -def 'None given' -lbl 'traitmapping' -element '&KEYVCV' @ClinicalAssertionID @TraitType MedGen@CUI MedGen@Name > ~{GENE_NAME}_traitmapping.txt

    >>>

    output {
        File traitmap  = "~{GENE_NAME}_traitmapping.txt"
    }

    runtime {
        memory: memSizeGB + " GB"
        cpu: threadCount
        disks: "local-disk " + diskSizeGB + " SSD"
        docker: "allisoncheney/cerfac_terra:clinvar"
        maxRetries: 1
        preemptible: 1
    }
}


task extract_clinvar_variants_traitset {
    input {
        String GENE_NAME
        File basicxml  
        Int memSizeGB = 10
        Int threadCount = 1
        Int diskSizeGB = 5*round(size(basicxml, "GB")) + 2

    }

    command <<<
        set -eux -o pipefail

        cat  ~{basicxml} |
        xtract -pattern VariationArchive -def 'NA' -KEYVCV VariationArchive@Accession \
            -group GermlineClassification/ConditionList \
                -block TraitSet -deq '\n' -def 'NA'   -TSID TraitSet@ID  -CONTRIB TraitSet@ContributesToAggregateClassification  -TSTYPE  TraitSet@Type \
                    -section Trait -deq '\n' -def 'NA'  -element '&KEYVCV'  '&TSID' '&TSTYPE' Trait@ID Trait@Type  '&CONTRIB'  \
                        -subset Trait/XRef -if XRef@DB -equals 'MedGen'  -element   XRef@ID  \
            -group SomaticClinicalImpact/ConditionList \
                -block TraitSet -deq '\n' -def 'NA'   -CONTRIB TraitSet@ContributesToAggregateClassification   -EVIDEN TraitSet@LowerLevelOfEvidence -TSYPE TraitSet@Type \
                    -section Trait -deq '\n' -def 'NA'  -element  '&KEYVCV'  '&TSID'  '&TSTYPE' Trait@ID Trait@Type '&CONTRIB' \
                        -subset Trait/XRef -if XRef@DB -equals 'MedGen'  -element  XRef@ID  \
            -group OncogenicityClassification/ConditionList \
                -block TraitSet -deq '\n' -def 'NA'   -CONTRIB TraitSet@ContributesToAggregateClassification   -EVIDEN TraitSet@LowerLevelOfEvidence -TSYPE TraitSet@Type \
                    -section Trait -deq '\n' -def 'NA'  -element  '&KEYVCV'  '&TSID'  '&TSTYPE' Trait@ID Trait@Type '&CONTRIB' \
                        -subset Trait/XRef -if XRef@DB -equals 'MedGen'  -element  XRef@ID    > ~{GENE_NAME}_traitset.txt


    >>>

    output {
        File traitset  = "~{GENE_NAME}_traitset.txt"
    }

    runtime {
        memory: memSizeGB + " GB"
        cpu: threadCount
        disks: "local-disk " + diskSizeGB + " SSD"
        docker: "allisoncheney/cerfac_terra:clinvar"
        maxRetries: 3
        preemptible: 1
    }
}




task extract_clinvar_variants_basic {
    input {
        String GENE_NAME
        File basicxml  
        Int memSizeGB = 10
        Int threadCount = 1
        Int diskSizeGB = 5*round(size(basicxml, "GB")) + 15

    }

    command <<<
        set -eux -o pipefail
        cat  ~{basicxml} |
        xtract -pattern VariationArchive -def "NA" -KEYVCV VariationArchive@Accession -KEYCHANGE "(unknown)" -KEYCONS "(unknown)" -KEYVNAME VariationArchive@VariationName -KEYVDC VariationArchive@DateCreated -KEYVDLU VariationArchive@DateLastUpdated -KEYVTYPE VariationArchive@VariationType -KEYSUBNUM VariationArchive@NumberOfSubmissions \
        -KEYGREVOV "(None given)" -KEYGCLASSOV "(None given)" -KEYOREVOV "(None given)" -KEYOCLASSOV "(None given)" -KEYSREVOV "(None given)" -KEYSCLASSOV "(None given)"\
            -group ClassifiedRecord/SimpleAllele/Location/SequenceLocation  -if SequenceLocation@forDisplay -equals true -def "NA" \
                -KEYASM SequenceLocation@Assembly -KEYCHR SequenceLocation@Chr  -KEYSTART SequenceLocation@start -KEYSTOP SequenceLocation@stop -KEYVCF SequenceLocation@positionVCF -KEYREFA SequenceLocation@referenceAlleleVCF -KEYALTA SequenceLocation@alternateAlleleVCF -KEYVLEN SequenceLocation@variantLength \
            -group ClassifiedRecord/Classifications -if GermlineClassification  -KEYGREVOV GermlineClassification/ReviewStatus -KEYGCLASSOV GermlineClassification/Description  \
            -group ClassifiedRecord/Classifications -if OncogenicityClassification  -KEYOREVOV OncogenicityClassification/ReviewStatus -KEYOCLASSOV OncogenicityClassification/Description  \
            -group ClassifiedRecord/Classifications -if SomaticClinicalImpact  -KEYSREVOV SomaticClinicalImpact/ReviewStatus -KEYSCLASSOV SomaticClinicalImpact/Description  \
            -group ClassifiedRecord/SimpleAllele/HGVSlist/HGVS -if NucleotideExpression@MANESelect -equals true \
                 -KEYCHANGE NucleotideExpression@change  -KEYCONS -first MolecularConsequence@Type \
            -group ClassifiedRecord/ClinicalAssertionList/ClinicalAssertion   \
                -deq "\n" -def "None given" -element "&KEYVCV" "&KEYVNAME" "&KEYVTYPE" "&KEYSUBNUM" ClinicalAssertion/ClinVarAccession@Accession "&KEYASM" "&KEYCHR" "&KEYSTART" "&KEYSTOP" "&KEYVCF" "&KEYREFA" "&KEYALTA" "&KEYVLEN" \
                "&KEYVDC"  "&KEYVDLU" ClinicalAssertion@DateCreated ClinicalAssertion@DateLastUpdated ClinicalAssertion@SubmissionDate \
                "&KEYGREVOV" "&KEYGCLASSOV" "&KEYOREVOV" "&KEYOCLASSOV" "&KEYSREVOV" "&KEYSCLASSOV" Classification/ReviewStatus Classification/GermlineClassification  \
                Classification/OncogenicityClassification Classification/SomaticClinicalImpact \
                "&KEYCONS"   "&KEYCHANGE" \
                Classification/Comment FunctionalConsequence@Value FunctionalConsequence/Comment  ClinicalAssertion@ID \
                    -block ObservedInList -def "None given"  \
                        -subset ObservedIn/Method -if ObsMethodAttribute/Attribute@Type -equals MethodResult -first ObsMethodAttribute/Attribute  |
        sed "s/&gt;/>/g" |
        sed "s/&lt;/</g" | 
        sed "s/â€™/'/g" | 
        sed "s/â€˜/'/g" | 
        sed "s/&amp;/&/g" > ~{GENE_NAME}_basic_res.txt


    >>>

    output {
        File basiccv  = "~{GENE_NAME}_basic_res.txt"
    }

    runtime {
        memory: memSizeGB + " GB"
        cpu: threadCount
        disks: "local-disk " + diskSizeGB + " SSD"
        docker: "allisoncheney/cerfac_terra:clinvar"
        maxRetries: 1
        preemptible: 1
    }
}




task merge_clinvar_variants {
    input {
        Int memSizeGB = 6
        Int threadCount = 1
        File basiccv
        File traitmap
        File traitset
        File python_script = "merge_clinvar_variants.py"
        Int diskSizeGB = 5*round(size(basiccv, "GB") + size(traitmap, 'GB') + size(traitset, 'GB')) + 5

    }
    #if you delete any columns make sure to change the number of columns included
    command <<<
        set -eux -o pipefail

        # Call the external Python script (localized by Cromwell)
        python3 "~{python_script}" "~{basiccv}" "~{traitmap}" "~{traitset}"

    >>>

    output {
        File clinvar_var = "clinvar_variants.csv"
        String clinvar_variants_count = read_string("clinvarcount.txt")
    }

    runtime {
        memory: memSizeGB + " GB"
        cpu: threadCount
        disks: "local-disk " + diskSizeGB + " SSD"
        docker: "allisoncheney/cerfac_terra:clinvar"
        maxRetries: 3
        preemptible: 1
    }
}




