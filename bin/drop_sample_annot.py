#!/usr/bin/env python3

import argparse
import re
from collections import OrderedDict
from pathlib import Path
import csv
import os
import pandas as pd


class PtSampleAnnotation:
    """PtSampleAnnotation class"""

    SAMPLE_ANNOTATION_COLUMNS = [
        "RNA_ID",
        "RNA_BAM_FILE",
        "DNA_VCF_FILE",
        "DNA_ID",
        "DROP_GROUP",
        "PAIRED_END",
        "COUNT_MODE",
        "COUNT_OVERLAPS",
        "SPLICE_COUNTS_DIR",
        "STRAND",
        "HPO_TERMS",
        "GENE_COUNTS_FILE",
        "GENE_ANNOTATION",
        "GENOME",
    ]

    def __init__(self, bam, sample, strandedness, single_end, gtf, count_file, out_file):
        """Write the Sample Annotation tsv file"""
        with open(out_file, "w") as tsv_file:
            fieldnames = self.SAMPLE_ANNOTATION_COLUMNS
            # sample_ids, sample_cnt_file = self.parse_header()
            writer = csv.DictWriter(tsv_file, fieldnames=fieldnames, delimiter="\t")

            writer.writeheader()

            for index, id in enumerate(sample):
                sa_dict = {}.fromkeys(fieldnames, "NA")
                sa_dict["RNA_ID"] = re.sub(r"[\[\],]", "", id)
                sa_dict["DROP_GROUP"] = "outrider,fraser"
                sa_dict["GENE_COUNTS_FILE"] = count_file
                sa_dict["GENE_ANNOTATION"] = Path(gtf).stem
                sa_dict["STRAND"] = re.sub(r"[\[\],]", "", strandedness[index])
                paired_end_func = lambda x: True if re.sub(r"[\[\],]", "", x).lower() == "false" else False
                sa_dict["PAIRED_END"] = paired_end_func(single_end[index])
                sa_dict["RNA_BAM_FILE"] = bam[index]
                writer.writerow(sa_dict)


def final_annot(count_file, ref_annot, out_file):
    df_pt = pd.read_csv("drop_pt_annot.tsv", sep="\t")
    df_ref = pd.read_csv(ref_annot, sep="\t")
    df_ref["GENE_COUNTS_FILE"] = count_file
    df_pt["COUNT_OVERLAPS"] = df_ref["COUNT_OVERLAPS"].iloc[0]
    df_pt["COUNT_MODE"] = df_ref["COUNT_MODE"].iloc[0]
    df_pt["HPO_TERMS"] = df_ref["HPO_TERMS"].iloc[0]
    df = pd.concat([df_pt, df_ref]).reset_index(drop=True)
    df.fillna("NA", inplace=True)
    df.to_csv(out_file, index=False, sep="\t")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        formatter_class=argparse.MetavarTypeHelpFormatter,
        description="""Generate DROP sample annotation for patients.""",
    )

    parser.add_argument(
        "--bam",
        type=str,
        nargs="+",
        help="bam files for the patient",
        required=True,
    )

    parser.add_argument(
        "--sample",
        type=str,
        nargs="+",
        help="corresponding sample name",
        required=True,
    )

    parser.add_argument(
        "--strandedness",
        type=str,
        nargs="+",
        help="strandedness of RNA",
        required=True,
    )

    parser.add_argument(
        "--single_end",
        type=str,
        nargs="+",
        help="is the sample paired end?",
        required=True,
    )

    parser.add_argument(
        "--gtf",
        type=str,
        help="Transcript annotation file in gtf format",
        required=True,
    )

    parser.add_argument(
        "--count_file", type=str, help="A tsv file of gene counts for all processed samples.", required=True
    )

    parser.add_argument(
        "--ref_annot",
        type=str,
        help="Path to reference annotation tsv",
        required=True,
    )

    parser.add_argument(
        "--output",
        type=str,
        help="Path to save to",
        required=True,
    )

    args = parser.parse_args()
    PtSampleAnnotation(
        args.bam, args.sample, args.strandedness, args.single_end, args.gtf, args.count_file, "drop_pt_annot.tsv"
    )
    final_annot(args.count_file, args.ref_annot, args.output)
