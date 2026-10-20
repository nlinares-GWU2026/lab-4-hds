"""Build the feature table (one row per patient) from cohort.db.

Run from repo root:
    python scripts/build_feature_table.py
Expects: data/cohort.db (see README.md for the download command)
Produces: outputs/feature_table.tsv"""

import sqlite3
import pandas as pd 

DB_PATH = "data/cohort.db"
BASE_SQL = "sql/query_3.sql"
GENE_COUNTS_SQL = "sql/query_1.sql"
OUTPUT_PATH = "outputs/feature_table.tsv"
GENES = ["TP53", "KRAS", "EGFR", "STK11", "KEAP1"]
GENE_COLUMNS = [f"{gene}_count" for gene in GENES]

def run_sql_file(con, path):
    """Run the query saved in a .sql file and return the result as a DataFrame."""
    with open(path) as f:
        return pd.read_sql(f.read(), con)

def reshape_gene_counts(gene_counts_long):
    """Reshape (patient, gene, count) rows into one row per patient, one column per gene.

    Query 1 already returns one row per patient and gene, so each cell has exactly
    one value to place; aggfunc="sum" is only a safeguard against duplicates.
    Patients with no protein-altering mmutation in any of the five genes have no
    gene to pivot on, so they are absent from this table; the merge adds them back.
    """
    wide = gene_counts_long.pivot_table(
        index="patient_id", columns="gene_symbol", values="n_mutations", aggfunc="sum"
    )
    wide = wide.reindex(columns=GENES)  # fixed gene order, even if a gene had no hits
    wide.columns = GENE_COLUMNS
    return wide.reset_index()

def main():
    con = sqlite3.connect(DB_PATH)

    n_patients = con.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
    base = run_sql_file(con, BASE_SQL)
    gene_counts_long = run_sql_file(con, GENE_COUNTS_SQL)
    con.close()

    gene_counts_wide = reshape_gene_counts(gene_counts_long)

    # LEFT merge keeps every patient from the base table.
    feature_table = base.merge(gene_counts_wide, on="patient_id", how="left")

    # Missing-data rule for gene counts: a patient absent from the wide table had no
    # protein altering mutation in these genes, which is a real zero, not "unknown".
    # Clinical columns (sex, age, stage) are NOT filled. They stay NA.
    feature_table[GENE_COLUMNS] = feature_table[GENE_COLUMNS].fillna(0).astype(int)

    # Checks: stop with an error if a join lost, or invented anything.
    total_long = gene_counts_long["n_mutations"].sum()
    total_wide = feature_table[GENE_COLUMNS].sum().sum()
    assert len(feature_table) == n_patients, "patient count changed after the joins"
    assert feature_table["patient_id"].is_unique, "a patient appears more than once"
    assert total_wide == total_long, "mutation counts changed during the reshape"

    print("Patient count audit")
    print(f"patients table: {n_patients}")
    print(f"after base query: {len(base)}")
    print(f"after adding gene counts: {len(feature_table)}")
    print(f"Mutation count audit (protein-altering, five genes)")
    print(f"long table total: {total_long}")
    print(f"wide table total: {total_wide}")
    print(f"Missing values (NA) per column")
    print(feature_table.isna().sum().to_string())

    feature_table.to_csv(OUTPUT_PATH, sep="\t", index=False, na_rep="NA")
    print(f"Wrote {OUTPUT_PATH}: {feature_table.shape[0]} rows x {feature_table.shape[1]} columns")

if __name__ == "__main__":
    main()