# Lab 4: Database-Driven Feature Table

This repo builds an analysis-ready feature table from a relational database of real lung adenocarcinoma tumor sequencing data (TCGA, via cBioPortal). SQL queries join the patient, sample, and mutation tables, and a Pythonh script reshapes the result into one row per patient (566 rows) with clinical columns, tumor columns, and protein-altering mutation counts for 5 lung cancer genes: TP53, KRAS, EGFR, STK11, and KEAP1. The output is a tab-separated file: `outputs/feature_table.tsv`.

## Contents

| File | Description |
|---|---|
| `scripts/build_feature_table.py` | Runs the SQL, reshapes the gene counts to wide format, checks the patient and mutation counts, and writes the feature table | 
| `sql/query_1.sql` | Query 1: protein-altering mutation counts per patient per gene (809 rows) | 
| `sql/query_2.sql` | Query 2: number of patients per tissue source site per tumor stage (142 rows)
| `sql/query_3.sql` | Query 3: one row per patient with sex, age, stage, tisse source site, and tumor mutation burden (566 rows) | 
| `outputs/feature_table.tsv` |Task 3: the final feature table with 566 patients x 11 columns | 
| `SCHEMA.md` | Task 1: the database tables, columns, keys, grain, and relationships | 
| `CHECKS.md` | Task 2: expected vs. actual row counts for each query | 
| `MISSING_DATA.md` | Task 4: how missing data and zero counts were handled, with patient counts before and after the joins |
| `DATA_DICITONARY.md` | Task 5: meaning, units, source table, and missing-value coding for every column of the feature table | 
| `AI_USAGE.md` | Which AI mdoel I used, for what, the output, and verification |
| `environment.yml` | The conda environment (Python 3.12, pandas 2.2, sqlite) | 

## Reproducing 

### 1. Get the code and create the environment
```bash
git clone https://github.com/nlinares-GWU2026/lab-4-hds.git
cd lab-4-hds
mamba env create -f environment.yml
conda activate lab-4-hds
```

### 2. Download the Database
The database (`cohort.db`) is not in this repo because the course asks us to laod data from its original source instead of committing a copy. It comes from the course repository (`gwcbi/applied-computing-HDS`) and is built from the TCGA Lung Adenocarcinoma PanCancer Atlas study on cBioPortal. The `data/` folder is in `.gitignore` so it does not exist after cloning and has to be created first. 
```bash
mkdir -p data outputs
curl -L -o data/cohort.db https://raw.githubusercontent.com/gwcbi/applied-computing-HDS/main/data/raw/lab4-cbioportal-luad/cohort.db
echo "6da3f91401918dda543aced9fa6f411dcecf204552cebfc6e54ab7d8f387e8e7  data/cohort.db" | sha256sum -c -
```

The last command compares the downloaded file's checksum (fingerprint identification of its contents) to the expected one. If it prints `OK`, the file is intact and you will be working from the same 566 patients.

## Build the Feature Table
```bash
python scripts/build_feature_table.py
```

**Expects:** `data/cohort.db` (from step 2) and the 3 query files in `sql/`. Run it from the repository root.

**Produces:** `outputs/feature_table.tsv`: a tab-separated file with 566 rows (one per patient) and 11 columns. Missing values are written as `NA.`

**Expected Result:** a patient count audit (566 patients in the `patients` table, 566 after the base query, 566 after adding the gene counts), a mutation count audit (746 protein-altering mutations in the 5 genes, in both the long and wide tables), the number of missing values per column, and a final line: 
```bash
Wrote outputs/feature_table.tsv: 566 rows x 11 columns
```

The script stops with an error if a join loses or repeats a patient, or if the mutation total changes during the reshape, so a silent mistake cannot pass quietly.

### 4. Run the SQL on its Own
```bash
sqlite3 -header -column data/cohort.db < sql/query1_gene_counts.sql
sqlite3 -header -column data/cohort.db < sql/query2_site_stage.sql
sqlite3 -header -column data/cohort.db < sql/query3_patient_base.sql
```
Query 1 returns 809 rows, Query 2 returns 142 rows, and Query 3 returns 566 rows. `CHECKS.md` explains how each expected count was worked out independently and why it matches. 

## Where each task is answered

| Task | Where |
|---|---|
| 1. Explore the schema | `SCHEMA.md` |
| 2. SQL queries and row counts | `sql/` and `CHECKS.md` |
| 3. Feature table | `scripts/build_feature_table.py` and `outputs/feature_table.tsv` |
| 4. Missing data | `MISSING_DATA.md` |
| 5. Data dictionary | `DATA_DICTIONARY.md` |

## Decisions Made
- **Protein-altering mutations:** every mutation whose `variant_classification` is anything other than `Silent.` Silent mutations change the DNA but not the protein, so they are excluded.
- **Zero vs. NA:** the five gene count columns use 0 when no protein-altering mutation was found, because every tumor was sequenced and the count of 0 is a real result. Sex, age, and stage stay `NA` when they were not recorded, because there is no justified value to fill it in. 
- **Missing clinical data:** all 52 patients from Washington University are missing sex, age, and stage, so the gaps come from one collection rather than being random. A further 19 patients (age) and 2 patients (stage) are missing values at other sites. No patients were dropped. 

## AI Usage
I used Claude (Sonnet 5.5) to help with this lab. `AI_USAGE.md` lists what it helped with and how I checked each result (independent row counts, hand-checked patients, and the checks built into the script).

