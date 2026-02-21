#!/usr/bin/env python3
import os
import io
import json
import string
import pandas as pd
import re
import logging
import sys

import gnomad
import hail as hl


def get_gnomad_variants(gene_name, chr_id, start_locus, end_locus, hail_mem_gb):
    hl.init(spark_conf={
        'spark.driver.memory': f"{hail_mem_gb}g",
        'spark.hadoop.google.cloud.auth.type': 'APPLICATION_DEFAULT'
    })

    start_pos = hl.int32(start_locus)
    stop_pos = hl.int32(end_locus)

    from gnomad.resources.grch38.gnomad import public_release
    v4exomes = public_release("exomes").ht()
    v4exomes.count()

    from gnomad.resources.grch38.gnomad import public_release
    v4genomes = public_release("genomes").ht()
    v4genomes.count()

    # Select relevant fields from exomes
    v4exomes_varid_sm = v4exomes.select(v4exomes.freq,
                                        v4exomes.vep.allele_string,
                                        v4exomes.vep.start,
                                        v4exomes.vep.end,
                                        v4exomes.vep.seq_region_name,
                                        v4exomes.vep.variant_class,
                                        v4exomes.in_silico_predictors.spliceai_ds_max,
                                        n_alt_alleles_exomes = v4exomes.allele_info.n_alt_alleles,
                                        txpt_biotype = v4exomes.vep.transcript_consequences.biotype,
                                        variant_effect = v4exomes.vep.transcript_consequences.consequence_terms,
                                        txpt_impact = v4exomes.vep.transcript_consequences.impact,
                                        VRS_Allele_IDs = v4exomes.info.vrs.VRS_Allele_IDs,
                                        allele_list_VRS = v4exomes.info.vrs.VRS_States,
                                        pos_VRS_starts = v4exomes.info.vrs.VRS_Starts,
                                        pos_VRS_stops = v4exomes.info.vrs.VRS_Ends,
                                        txpt_amino_acids = v4exomes.vep.transcript_consequences.amino_acids,
                                        txpt_appris = v4exomes.vep.transcript_consequences.appris,
                                        txpt_canonical = v4exomes.vep.transcript_consequences.canonical,
                                        txpt_distance = v4exomes.vep.transcript_consequences.distance,
                                        txpt_domains = v4exomes.vep.transcript_consequences.domains,
                                        txpt_exon = v4exomes.vep.transcript_consequences.exon,
                                        txpt_hgvsc = v4exomes.vep.transcript_consequences.hgvsc,
                                        txpt_hgvsp = v4exomes.vep.transcript_consequences.hgvsp,
                                        txpt_gene_pheno = v4exomes.vep.transcript_consequences.gene_pheno,
                                        txpt_gene_symbol = v4exomes.vep.transcript_consequences.gene_symbol,
                                        txpt_intron = v4exomes.vep.transcript_consequences.intron,
                                        txpt_lof = v4exomes.vep.transcript_consequences.lof,
                                        txpt_lof_flags = v4exomes.vep.transcript_consequences.lof_flags,
                                        txpt_lof_filter = v4exomes.vep.transcript_consequences.lof_filter,
                                        txpt_lof_info = v4exomes.vep.transcript_consequences.lof_info,
                                        txpt_mane_select = v4exomes.vep.transcript_consequences.mane_select,
                                        txpt_mane_plus_clinical = v4exomes.vep.transcript_consequences.mane_plus_clinical,
                                        txpt_protein_start = v4exomes.vep.transcript_consequences.protein_start,
                                        txpt_protein_end = v4exomes.vep.transcript_consequences.protein_end,
                                        txpt_transcript_id = v4exomes.vep.transcript_consequences.transcript_id,
                                        txpt_uniprot_isoform = v4exomes.vep.transcript_consequences.uniprot_isoform
                                        )

    # Select relevant fields from genomes
    v4genomes_varid_sm = v4genomes.select(v4genomes.freq,
                                        v4genomes.vep.allele_string,
                                        v4genomes.vep.start,
                                        v4genomes.vep.end,
                                        v4genomes.vep.seq_region_name,
                                        v4genomes.vep.variant_class,
                                        v4genomes.in_silico_predictors.spliceai_ds_max,
                                        VRS_Allele_IDs = v4genomes.info.vrs.VRS_Allele_IDs,
                                        allele_list_VRS = v4genomes.info.vrs.VRS_States,
                                        pos_VRS_starts = v4genomes.info.vrs.VRS_Starts,
                                        pos_VRS_stops = v4genomes.info.vrs.VRS_Ends,
                                        n_alt_alleles_genomes = v4genomes.allele_info.n_alt_alleles,
                                        txpt_biotype = v4genomes.vep.transcript_consequences.biotype,
                                        variant_effect = v4genomes.vep.transcript_consequences.consequence_terms,
                                        txpt_impact = v4genomes.vep.transcript_consequences.impact,
                                        txpt_amino_acids = v4genomes.vep.transcript_consequences.amino_acids,
                                        txpt_appris = v4genomes.vep.transcript_consequences.appris,
                                        txpt_canonical = v4genomes.vep.transcript_consequences.canonical,
                                        txpt_distance = v4genomes.vep.transcript_consequences.distance,
                                        txpt_domains = v4genomes.vep.transcript_consequences.domains,
                                        txpt_exon = v4genomes.vep.transcript_consequences.exon,
                                        txpt_hgvsc = v4genomes.vep.transcript_consequences.hgvsc,
                                        txpt_hgvsp = v4genomes.vep.transcript_consequences.hgvsp,
                                        txpt_gene_pheno = v4genomes.vep.transcript_consequences.gene_pheno,
                                        txpt_gene_symbol = v4genomes.vep.transcript_consequences.gene_symbol,
                                        txpt_intron = v4genomes.vep.transcript_consequences.intron,
                                        txpt_lof = v4genomes.vep.transcript_consequences.lof,
                                        txpt_lof_flags = v4genomes.vep.transcript_consequences.lof_flags,
                                        txpt_lof_filter = v4genomes.vep.transcript_consequences.lof_filter,
                                        txpt_lof_info = v4genomes.vep.transcript_consequences.lof_info,
                                        txpt_mane_select = v4genomes.vep.transcript_consequences.mane_select,
                                        txpt_mane_plus_clinical = v4genomes.vep.transcript_consequences.mane_plus_clinical,
                                        txpt_protein_start = v4genomes.vep.transcript_consequences.protein_start,
                                        txpt_protein_end = v4genomes.vep.transcript_consequences.protein_end,
                                        txpt_transcript_id = v4genomes.vep.transcript_consequences.transcript_id,
                                        txpt_uniprot_isoform = v4genomes.vep.transcript_consequences.uniprot_isoform
                                        )

    # Annotate population frequencies for exomes
    v4exomes_varid_sm = v4exomes_varid_sm.annotate(exome_freq_main_adj_afr=v4exomes_varid_sm.freq[v4exomes_varid_sm.freq_index_dict['afr_adj']])
    v4exomes_varid_sm = v4exomes_varid_sm.annotate(exome_freq_main_adj_amr=v4exomes_varid_sm.freq[v4exomes_varid_sm.freq_index_dict['amr_adj']])
    v4exomes_varid_sm = v4exomes_varid_sm.annotate(exome_freq_main_adj_eas=v4exomes_varid_sm.freq[v4exomes_varid_sm.freq_index_dict['eas_adj']])
    v4exomes_varid_sm = v4exomes_varid_sm.annotate(exome_freq_main_adj_nfe=v4exomes_varid_sm.freq[v4exomes_varid_sm.freq_index_dict['nfe_adj']])
    v4exomes_varid_sm = v4exomes_varid_sm.annotate(exome_freq_main_adj_rmi=v4exomes_varid_sm.freq[v4exomes_varid_sm.freq_index_dict['remaining_adj']])
    v4exomes_varid_sm = v4exomes_varid_sm.annotate(exome_freq_main_adj_sas=v4exomes_varid_sm.freq[v4exomes_varid_sm.freq_index_dict['sas_adj']])
    v4exomes_varid_sm = v4exomes_varid_sm.annotate(exome_freq_main_adj_mid=v4exomes_varid_sm.freq[v4exomes_varid_sm.freq_index_dict['mid_adj']])
    v4exomes_varid_sm = v4exomes_varid_sm.annotate(exome_freq_main_adj_fin=v4exomes_varid_sm.freq[v4exomes_varid_sm.freq_index_dict['fin_adj']])
    v4exomes_varid_sm = v4exomes_varid_sm.annotate(exome_freq_main_adj_asj=v4exomes_varid_sm.freq[v4exomes_varid_sm.freq_index_dict['asj_adj']])

    # Annotate population frequencies for genomes
    v4genomes_varid_sm = v4genomes_varid_sm.annotate(genome_freq_adj_afr=v4genomes_varid_sm.freq[v4genomes_varid_sm.freq_index_dict['afr_adj']])
    v4genomes_varid_sm = v4genomes_varid_sm.annotate(genome_freq_adj_amr=v4genomes_varid_sm.freq[v4genomes_varid_sm.freq_index_dict['amr_adj']])
    v4genomes_varid_sm = v4genomes_varid_sm.annotate(genome_freq_adj_eas=v4genomes_varid_sm.freq[v4genomes_varid_sm.freq_index_dict['eas_adj']])
    v4genomes_varid_sm = v4genomes_varid_sm.annotate(genome_freq_adj_nfe=v4genomes_varid_sm.freq[v4genomes_varid_sm.freq_index_dict['nfe_adj']])
    v4genomes_varid_sm = v4genomes_varid_sm.annotate(genome_freq_adj_rmi=v4genomes_varid_sm.freq[v4genomes_varid_sm.freq_index_dict['remaining_adj']])
    v4genomes_varid_sm = v4genomes_varid_sm.annotate(genome_freq_adj_sas=v4genomes_varid_sm.freq[v4genomes_varid_sm.freq_index_dict['sas_adj']])
    v4genomes_varid_sm = v4genomes_varid_sm.annotate(genome_freq_adj_mid=v4genomes_varid_sm.freq[v4genomes_varid_sm.freq_index_dict['mid_adj']])
    v4genomes_varid_sm = v4genomes_varid_sm.annotate(genome_freq_adj_fin=v4genomes_varid_sm.freq[v4genomes_varid_sm.freq_index_dict['fin_adj']])
    v4genomes_varid_sm = v4genomes_varid_sm.annotate(genome_freq_adj_asj=v4genomes_varid_sm.freq[v4genomes_varid_sm.freq_index_dict['asj_adj']])

    # Helper functions for variant ID creation
    def get_ref_genome(locus: hl.expr.LocusExpression):
        ref_gen = hl.str(gnomad.utils.reference_genome.get_reference_genome(locus).name)
        return ref_gen

    def normalized_contig(contig: hl.expr.StringExpression) -> hl.expr.StringExpression:
        return hl.rbind(hl.str(contig).replace("^chr", ""), lambda c: hl.if_else(c == "MT", "M", c))

    def chromosome_id(locus: hl.expr.LocusExpression, alleles: hl.expr.ArrayExpression, max_length: int = None):
        chr_id = hl.str(locus.contig)
        if max_length is not None:
            return chr_id[0:max_length]
        return chr_id

    def get_start_pos(locus: hl.expr.LocusExpression, alleles: hl.expr.ArrayExpression):
        start_pos = hl.int32(locus.position)
        return start_pos

    def get_end_pos_alt(locus: hl.expr.LocusExpression, alleles: hl.expr.ArrayExpression):
        alt_allele = hl.len(alleles[1])
        inmd = hl.int32(alt_allele - 1)
        end_alt = hl.int32(locus.position) + inmd
        return end_alt

    def get_alt_allele_len(locus: hl.expr.LocusExpression, alleles: hl.expr.ArrayExpression):
        return hl.len(alleles[1])

    def get_ref_allele_len(locus: hl.expr.LocusExpression, alleles: hl.expr.ArrayExpression):
        return hl.len(alleles[0])

    def get_alt_allele(locus: hl.expr.LocusExpression, alleles: hl.expr.ArrayExpression):
        return hl.str(alleles[1])

    def get_ref_allele(locus: hl.expr.LocusExpression, alleles: hl.expr.ArrayExpression):
        return hl.str(alleles[0])

    def get_VRS_start_ref(pos_VRS_starts: hl.expr.ArrayNumericExpression):
        return hl.str(pos_VRS_starts[0])

    def get_VRS_start_alt(locus: hl.expr.LocusExpression, pos_VRS_starts: hl.expr.ArrayNumericExpression):
        return hl.str(pos_VRS_starts[1])

    def get_VRS_stop_ref(pos_VRS_stops: hl.expr.ArrayNumericExpression):
        return hl.str(pos_VRS_stops[0])

    def get_VRS_stop_alt(pos_VRS_stops: hl.expr.ArrayNumericExpression):
        return hl.str(pos_VRS_stops[1])

    def variant_idCERFAC_VCF(locus: hl.expr.LocusExpression, alleles: hl.expr.ArrayExpression, max_length: int = None):
        var_id = hl.str(locus.contig) + "-" + hl.str(locus.position) + "-" + alleles[0] + "-" + alleles[1]
        if max_length is not None:
            return var_id[0:max_length]
        return var_id

    # Annotate reference genome
    v4genomes_varid_sm = v4genomes_varid_sm.annotate(ref_genome=get_ref_genome(v4genomes_varid_sm.locus))

    # Filter to gene region
    chr_string = "chr" + chr_id
    filtered_v4exomes = v4exomes_varid_sm.filter(v4exomes_varid_sm.locus.contig == chr_string)
    filtered_v4genomes = v4genomes_varid_sm.filter(v4genomes_varid_sm.locus.contig == chr_string)
    exomes_select = hl.filter_intervals(filtered_v4exomes, [hl.locus_interval(chr_string, start_pos, stop_pos, reference_genome='GRCh38')])
    genomes_select = hl.filter_intervals(filtered_v4genomes, [hl.locus_interval(chr_string, start_pos, stop_pos, reference_genome='GRCh38')])

    # Join exomes and genomes
    joined_gnomad_inner = genomes_select.join(exomes_select, how='inner')
    joined_gnomad_inner = joined_gnomad_inner.annotate(exorgen="both")
    joined_gnomad_inner = joined_gnomad_inner.drop(*(x for x in joined_gnomad_inner.row if re.search(r'_1', x)))

    genomes_select_aj = genomes_select.anti_join(exomes_select)
    genomes_select_aj = genomes_select_aj.annotate(exorgen="genomes")

    exomes_select_aj = exomes_select.anti_join(genomes_select)
    exomes_select_aj = exomes_select_aj.annotate(exorgen="exomes")

    # Drop freq column and flatten
    joined_gnomad_inner = joined_gnomad_inner.drop('freq')
    exomes_select_aj = exomes_select_aj.drop('freq')
    genomes_select_aj = genomes_select_aj.drop('freq')

    joined_gnomad_inner = joined_gnomad_inner.flatten()
    exomes_select_aj = exomes_select_aj.flatten()
    genomes_select_aj = genomes_select_aj.flatten()

    # Union all datasets
    gnomad_union_1 = exomes_select_aj.union(joined_gnomad_inner, unify=True)
    gnomad_union_1.count()

    gnomad_union = gnomad_union_1.union(genomes_select_aj, unify=True)

    # Add annotations
    gnomad_union = gnomad_union.annotate(ref_genome=get_ref_genome(gnomad_union.locus))
    gnomad_union = gnomad_union.annotate(chr_id=chromosome_id(gnomad_union.locus, gnomad_union.alleles))
    gnomad_union = gnomad_union.annotate(CERFAC_variant_id_VCF=variant_idCERFAC_VCF(gnomad_union.locus, gnomad_union.alleles))
    gnomad_union = gnomad_union.annotate(allele_ref=get_ref_allele(gnomad_union.locus, gnomad_union.alleles))
    gnomad_union = gnomad_union.annotate(allele_alt=get_alt_allele(gnomad_union.locus, gnomad_union.alleles))
    gnomad_union = gnomad_union.annotate(variant_length_ref=get_ref_allele_len(gnomad_union.locus, gnomad_union.alleles))
    gnomad_union = gnomad_union.annotate(variant_length_alt=get_alt_allele_len(gnomad_union.locus, gnomad_union.alleles))
    gnomad_union = gnomad_union.annotate(pos_start_alt_vrs=get_VRS_start_alt(gnomad_union.locus, gnomad_union.pos_VRS_starts))
    gnomad_union = gnomad_union.annotate(pos_start_ref_vrs=get_VRS_start_ref(gnomad_union.pos_VRS_starts))
    gnomad_union = gnomad_union.annotate(pos_stop_alt_vrs=get_VRS_stop_alt(gnomad_union.pos_VRS_stops))
    gnomad_union = gnomad_union.annotate(pos_stop_ref_vrs=get_VRS_stop_ref(gnomad_union.pos_VRS_stops))

    # Convert to pandas
    gnomad_union_df = gnomad_union.to_pandas(flatten=True)
    gnomad_union_df = gnomad_union_df.sort_index(axis=1)

    # Explode transcript columns
    badcols = [
        'txpt_amino_acids', 'txpt_appris', 'txpt_biotype', 'txpt_canonical',
        'variant_effect', 'txpt_distance', 'txpt_domains', 'txpt_exon',
        'txpt_hgvsc','txpt_hgvsp',
        'txpt_gene_pheno', 'txpt_gene_symbol', 'txpt_impact', 'txpt_intron',
        'txpt_lof', 'txpt_lof_filter', 'txpt_lof_flags', 'txpt_lof_info',
        'txpt_mane_plus_clinical', 'txpt_mane_select', 'txpt_protein_end',
        'txpt_protein_start', 'txpt_transcript_id', 'txpt_uniprot_isoform']
    gnomad_union_df = gnomad_union_df.explode(badcols)

    # Filter to canonical transcripts and target gene
    gnomad_union_df = gnomad_union_df[gnomad_union_df.txpt_canonical == 1]
    gnomad_union_df = gnomad_union_df.dropna(subset=['txpt_gene_symbol'])
    gnomad_union_df = gnomad_union_df[gnomad_union_df.txpt_gene_symbol == gene_name]
    gnomad_union_df = gnomad_union_df[gnomad_union_df['txpt_mane_select'].str.startswith('NM')]

    # Clean variant effect column
    gnomad_union_df[['variant_effect']] = gnomad_union_df[['variant_effect']].astype('str')
    gnomad_union_df.loc[:, ('variant_effect')] = gnomad_union_df.loc[:, ('variant_effect')].astype('str').str.replace('[','')
    gnomad_union_df.loc[:, ('variant_effect')] = gnomad_union_df.loc[:, ('variant_effect')].astype('str').str.replace(']','')
    gnomad_union_df.loc[:, ('variant_effect')] = gnomad_union_df.loc[:, ('variant_effect')].astype('str').str.replace("'","")

    # Explode uniprot isoforms
    badcols = ['txpt_uniprot_isoform']
    gnomad_union_df = gnomad_union_df.explode(badcols)

    # Filter out non-coding variants
    gnomad_union_df = gnomad_union_df[gnomad_union_df.variant_effect != "upstream_gene_variant"]
    gnomad_union_df = gnomad_union_df[gnomad_union_df.variant_effect != "5_prime_UTR_variant"]
    gnomad_union_df = gnomad_union_df[gnomad_union_df.variant_effect != "3_prime_UTR_variant"]
    gnomad_union_df = gnomad_union_df[gnomad_union_df.variant_effect != "intron_variant"]

    # Create HGVS identifiers
    gnomad_union_df[['txpt_hgvsc']] = gnomad_union_df[['txpt_hgvsc']].astype('str')
    gnomad_union_df['CERFAC_variant_id_HGVS_long'] = gnomad_union_df[['ref_genome', 'locus','txpt_hgvsc']].astype(str).agg(':'.join, axis=1)
    gnomad_union_df['txpt_hgvsc_short'] = gnomad_union_df['txpt_hgvsc'].str.split(pat=":", n=1, regex=False).str.get(1)
    gnomad_union_df['hgvs_pro'] = gnomad_union_df['txpt_hgvsp'].str.split(pat=":", n=1, regex=False).str.get(1)
    gnomad_union_df['CERFAC_variant_id_HGVS_short'] = gnomad_union_df[['ref_genome','locus','txpt_hgvsc_short']].astype(str).agg(':'.join, axis=1)
    gnomad_union_df[['CERFAC_variant_id_VCF']] = gnomad_union_df[['CERFAC_variant_id_VCF']].astype('str')
    gnomad_union_df['CERFAC_variant_id_VCF'] = gnomad_union_df[['CERFAC_variant_id_VCF']].astype('str').replace("chr", "")

    # Drop unnecessary columns
    gnomad_union_df = gnomad_union_df.drop(columns=['txpt_appris', 'txpt_distance', 'txpt_biotype', 'txpt_canonical',
        'txpt_gene_pheno', 'txpt_gene_symbol', 'seq_region_name','chr_id','ref_genome',
        'txpt_protein_end', 'txpt_protein_start'])

    gnomad_union_df[['txpt_exon']] = gnomad_union_df[['txpt_exon']].astype('str')
    gnomad_union_df[['txpt_intron']] = gnomad_union_df[['txpt_intron']].astype('str')

    # Count variants
    gnomad_variants_count_pd = str(gnomad_union_df['txpt_hgvsc_short'].nunique())
    with open("gnomadcount.txt", 'w') as x_file:
        x_file.write(gnomad_variants_count_pd)

    # Rename and sort columns
    gnomad_union_df = gnomad_union_df.rename(columns={"alleles": "allele_list", "locus": "pos_VCF", "exorgen": "set"}, errors='raise')
    gnomad_union_df = gnomad_union_df.rename(columns={"start": "pos_start_vep", "end": "pos_stop_vep"}, errors='raise')
    gnomad_union_df = gnomad_union_df.sort_index(axis=1)
    gnomad_union_df['variant_source'] = "gnomAD"
    gnomad_union_df = gnomad_union_df.add_suffix('_gnomad')
    gnomad_union_df['HGVS_cDNA_ID_gnomad'] = gnomad_union_df[['txpt_mane_select_gnomad', 'txpt_hgvsc_short_gnomad']].astype(str).agg(':'.join, axis=1)

    # Output to CSV
    gnomad_union_df.to_csv(f"{gene_name}_gnomad_variants_MANE.csv", sep=',', index=False)


if __name__ == "__main__":
    if len(sys.argv) != 6:
        print("Usage: get_gnomad_variants.py <gene_name> <chr_id> <start_locus> <end_locus> <hail_mem_gb>")
        sys.exit(1)

    gene_name = sys.argv[1]
    chr_id = sys.argv[2]
    start_locus = int(sys.argv[3])
    end_locus = int(sys.argv[4])
    hail_mem_gb = int(sys.argv[5])

    get_gnomad_variants(gene_name, chr_id, start_locus, end_locus, hail_mem_gb)
