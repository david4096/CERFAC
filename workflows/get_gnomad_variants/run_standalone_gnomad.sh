java -Dconfig.file=/home/mcline/CERFAC/cromwell.conf \
     -jar /home/mcline/bin/cromwell.jar run \
     /home/mcline/CERFAC/workflows/get_gnomad_variants/get_gnomad_variants.wdl \
     --inputs /home/mcline/CERFAC/workflows/get_gnomad_variants/get_gnomad_variants.brca1.input.json \
     2>&1
