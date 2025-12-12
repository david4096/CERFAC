#!/usr/bin/env python3
import pandas as pd
import sys

def merge_clinvar_variants(basiccv_path, traitmap_path, traitset_path):
    """
    Merge ClinVar variants data from three input files.

    Args:
        basiccv_path: Path to basic ClinVar data file
        traitmap_path: Path to trait mapping file
        traitset_path: Path to trait set file
    """
    Gene_CV_basic = pd.read_csv(basiccv_path, delimiter="\t", engine='python',
                                names =["VCV_ID", "ClinVar_variant_ID", "variant_class","number_submissions", "SCV_ID",
                                    "assembly", "Chr", "start", "stop",  "pos_VCF", "ref", "alt","variant_length",
                                    "date_variant_created", "date_variant_updated",  "date_submission_created", "date_submission_updated","date_submitted",
                                    "overall_germline_review_status","overall_germline_classification","overall_onco_review_status","overall_oncogenicity_classification","overall_som_review_status","overall_somatic_classification",
                                    "submission_review_status","submission_germline_classification", "submission_oncogenicity_classification", "submission_somatic_classification",
                                    "variant_effect","txpt_hgvsc",
                                    "comment",
                                    "functional_category", "functional_comment",
                                    "CA_ID", "functional_result", "extra1", "extra2"] ,   header=None, keep_default_na=False)
    Gene_CV_basic.iloc[:, 0:35]



    trait_set = pd.read_csv(traitset_path, delimiter="\t",
                        names = ["VCV_ID", "TraitSet_ID","TS_Type" , "Trait_ID","Trait_Type",  "ContributesToAggregateClassification","MG_ID" ] )
    trait_set['TraitSet_ID'] = trait_set['TraitSet_ID'].fillna("none")
    trait_set[['TraitSet_ID' ]] = trait_set[['TraitSet_ID' ]].astype('str')
    trait_set[['Trait_ID' ]] = trait_set[['Trait_ID' ]].astype('str')
    trait_set['MG_ID'] = trait_set['MG_ID'].fillna("none")
    trait_set['Trait_Type'] = trait_set['Trait_Type'].fillna("none")
    trait_set['TS_Type'] = trait_set['TS_Type'].fillna("none")
    trait_set=trait_set.sort_values([ "VCV_ID", "MG_ID"])
    trait_set['MG_ID'] = trait_set[["VCV_ID", "TraitSet_ID","TS_Type" , "Trait_ID","Trait_Type",  "ContributesToAggregateClassification","MG_ID"]].groupby(["VCV_ID", "TraitSet_ID" ])['MG_ID'].transform(lambda x: '_'.join(x))
    trait_set['Trait_ID'] = trait_set[["VCV_ID", "TraitSet_ID","TS_Type" , "Trait_ID","Trait_Type",  "ContributesToAggregateClassification","MG_ID"]].groupby(["VCV_ID", "TraitSet_ID" ])['Trait_ID'].transform(lambda x: '&'.join(x))
    trait_set =  trait_set[["VCV_ID", "TraitSet_ID","TS_Type" , "Trait_ID","Trait_Type",  "ContributesToAggregateClassification","MG_ID"]].drop_duplicates()


    trait_map = pd.read_csv(traitmap_path, delimiter="\t",
                        names = ["label", "VCV_ID", "CA_ID", "Trait_Type", "MG_ID", "MG_disease_name"] )
    trait_map['MG_ID'] = trait_map['MG_ID'].fillna("none")
    trait_map['Trait_Type'] = trait_map['Trait_Type'].fillna("none")
    trait_map['MG_disease_name'] = trait_map['MG_disease_name'].fillna("none")
    trait_map[['CA_ID' ]] = trait_map[['CA_ID' ]].astype('str')
    trait_map = trait_map.sort_values([ "VCV_ID", "MG_ID"])
    trait_map['MG_ID'] = trait_map[["label", "VCV_ID", "CA_ID", "Trait_Type", "MG_ID", "MG_disease_name"]].groupby(["label", "VCV_ID","Trait_Type", "CA_ID"])['MG_ID'].transform(lambda x: '_'.join(x))
    trait_map['MG_disease_name'] = trait_map[["label", "VCV_ID", "CA_ID", "Trait_Type", "MG_ID", "MG_disease_name"]].groupby(["label", "VCV_ID","Trait_Type", "CA_ID","MG_ID"])['MG_disease_name'].transform(lambda x: '&'.join(x))
    trait_map = trait_map[["label", "VCV_ID", "CA_ID", "Trait_Type", "MG_ID", "MG_disease_name"]].drop_duplicates()


    trait_comb = pd.merge(trait_set, trait_map, how='outer', on=["VCV_ID", "MG_ID"])
    trait_comb['MG_ID'] = trait_comb['MG_ID'].fillna("none")
    trait_comb['CA_ID'] = trait_comb['CA_ID'].fillna("none")
    trait_comb['MG_disease_name'] = trait_comb['MG_disease_name'].fillna("none")
    trait_comb['TraitSet_ID'] = trait_comb['TraitSet_ID'].fillna("none")
    trait_comb['Trait_Type_y'] = trait_comb['Trait_Type_y'].fillna("none")
    trait_comb['Trait_Type_x'] = trait_comb['Trait_Type_x'].fillna("none")
    trait_comb['TS_Type'] = trait_comb['TS_Type'].fillna("none")
    trait_comb = trait_comb[trait_comb.CA_ID != "none"]
    trait_comb = trait_comb.drop(trait_comb[(trait_comb['TraitSet_ID'] == "none") & (trait_comb['Trait_Type_y'] == "Finding")].index)

    Gene_CV_basic['CA_ID'] = Gene_CV_basic['CA_ID'].fillna("none")
    Gene_CV_basic[['CA_ID' ]] = Gene_CV_basic[['CA_ID' ]].astype('str')
    trait_comb[['CA_ID' ]] = trait_comb[['CA_ID' ]].astype('str')

    clinvar_complete = pd.merge(Gene_CV_basic, trait_comb, how='outer', on=["VCV_ID", "CA_ID"])
    clinvar_complete['Chr'] = clinvar_complete['Chr'].astype(str)
    clinvar_complete['CERFAC_variant_id_VCF'] = clinvar_complete[['Chr','pos_VCF','ref','alt' ]].astype(str).agg('-'.join, axis=1)
    clinvar_complete['Chr'] = 'chr' + clinvar_complete['Chr'].astype(str)
    clinvar_complete['CERFAC_variant_id_HGVS_long'] = clinvar_complete[['assembly', 'Chr','ClinVar_variant_ID' ]].astype(str).agg(':'.join, axis=1)
    clinvar_complete['CERFAC_variant_id_HGVS_short'] = clinvar_complete[['assembly', 'Chr','pos_VCF','txpt_hgvsc' ]].astype(str).agg(':'.join, axis=1)
    clinvar_complete['txpt_hgvsc_from_ID'] = clinvar_complete['ClinVar_variant_ID'].str.split(pat=":", n=1,  regex=False).str.get(1)
    clinvar_complete['txpt_hgvsc_from_ID_no_pro'] = clinvar_complete['txpt_hgvsc_from_ID'].str.split(pat=" ", n=1,  regex=False).str.get(0)
    clinvar_complete['hgvs_pro'] = clinvar_complete['ClinVar_variant_ID'].str.split(pat=" ", n=1,  regex=False).str.get(1)
    clinvar_complete['hgvs_pro'] = clinvar_complete['hgvs_pro'].replace(regex=True, to_replace='\)', value='')
    clinvar_complete['hgvs_pro'] = clinvar_complete['hgvs_pro'].replace(regex=True, to_replace='\(', value='')


    cols = ['VCV_ID','txpt_hgvsc_from_ID','hgvs_pro',
    'CERFAC_variant_id_VCF',
    'CERFAC_variant_id_HGVS_long',
    'CERFAC_variant_id_HGVS_short',
    'ClinVar_variant_ID','number_submissions', 'SCV_ID',
    'start','stop','pos_VCF','ref','alt',
    'variant_length', 'MG_disease_name','ContributesToAggregateClassification',
    'variant_class', 'variant_effect','txpt_hgvsc',
    'overall_germline_review_status','overall_germline_classification','submission_review_status','submission_germline_classification',
    'overall_onco_review_status','overall_oncogenicity_classification','submission_oncogenicity_classification',
    'overall_som_review_status','overall_somatic_classification','submission_somatic_classification',
    'comment',
    'functional_category','functional_comment','functional_result',
    'date_variant_created', 'date_variant_updated',  'date_submission_created', 'date_submission_updated', 'date_submitted', 'txpt_hgvsc_from_ID_no_pro']

    clinvar_complete = clinvar_complete[cols]


    clinvar_complete = clinvar_complete[clinvar_complete.variant_effect != "5 prime UTR variant"]
    clinvar_complete = clinvar_complete[clinvar_complete.variant_effect != "3 prime UTR variant"]

    clinvar_variants_count_pd = str(clinvar_complete['txpt_hgvsc'].nunique())
    file_name = "clinvarcount.txt"
    with open(file_name, 'w') as x_file:
        x_file.write(clinvar_variants_count_pd)
    clinvar_complete = clinvar_complete.rename(columns={"ref": "allele_ref",  "alt": "allele_alt",   "start": "pos_start",   "stop": "pos_stop"}, errors='raise')
    clinvar_complete['variant_source']="ClinVar"
    clinvar_complete = clinvar_complete[clinvar_complete.variant_effect != "splice donor variant"]
    clinvar_complete = clinvar_complete[clinvar_complete.variant_effect != "splice acceptor variant"]
    clinvar_complete = clinvar_complete[clinvar_complete.variant_effect != "intron variant"]

    clinvar_complete = clinvar_complete.add_suffix('_clinvar')

    clinvar_complete['txpt_ref_from_ID'] = clinvar_complete['ClinVar_variant_ID_clinvar'].str.split(pat=":", n=1,  regex=False).str.get(0)

    clinvar_complete['ref_txpt_clinvar'] = clinvar_complete['txpt_ref_from_ID'].str.split(pat="(", n=1,  regex=False).str.get(0)
    clinvar_complete['hgvs_cdna_clinvar'] = clinvar_complete[['ref_txpt_clinvar', 'txpt_hgvsc_clinvar' ]].astype(str).agg(':'.join, axis=1)
    clinvar_complete['hgvs_cdna_clinvar_from_ID'] = clinvar_complete[['ref_txpt_clinvar', 'txpt_hgvsc_from_ID_no_pro_clinvar' ]].astype(str).agg(':'.join, axis=1)


    clinvar_complete.to_csv("clinvar_variants.csv", sep=',', index=False )


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: merge_clinvar_variants.py <basiccv_file> <traitmap_file> <traitset_file>")
        sys.exit(1)

    basiccv_path = sys.argv[1]
    traitmap_path = sys.argv[2]
    traitset_path = sys.argv[3]

    merge_clinvar_variants(basiccv_path, traitmap_path, traitset_path)
