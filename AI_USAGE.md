# AI Usage

**Model:** Claude Sonnet 5.5

## Entry 1: Schema exploring
- **What I asked (verbatim):** "Can you write me commands in the sqlite3 CLI that queries: 1. Can a patient have more than one sample?, 2. Are there orphan samples or samples that matches no patient?, 3. Finds if there are patients with no sample., 4. Finds if there are mutations pointing at a sample that does not exist. 5. Finds if there are mutations pointing at a nonexistent gene., 6. Finds if there are samples with no mutations at all., 7. Describes the grain."
- **Output (verbatim):** 
Test the relationships
Before running each query below, write your prediction on paper or in a note. There are no tricks. It's just practice at noticing when a result surprises you.
Query 1: Can a patient have more than one sample? This groups samples by patient and shows the largest group first:
SELECT patient_id, COUNT(*) AS n_samples FROM samples GROUP BY patient_id ORDER BY n_samples DESC LIMIT 3;

If the top number is 1, every patient has exactly one sample.
Query 2: Orphan samples:
SELECT COUNT(*) AS orphan_samples FROM samples s LEFT JOIN patients p ON p.patient_id = s.patient_id WHERE p.patient_id IS NULL;

Query 3: Patients with no sample. Same pattern, from the other direction:
SELECT COUNT(*) AS patients_without_sample FROM patients p LEFT JOIN samples s ON s.patient_id = p.patient_id WHERE s.sample_id IS NULL;

Query 4: Mutations pointing at a nonexistent sample:
SELECT COUNT(*) AS orphan_mutations_sample FROM mutations m LEFT JOIN samples s ON s.sample_id = m.sample_id WHERE s.sample_id IS NULL;

Query 5: Mutations pointing at a nonexistent gene:
SELECT COUNT(*) AS orphan_mutations_gene FROM mutations m LEFT JOIN genes g ON g.gene_symbol = m.gene_symbol WHERE g.gene_symbol IS NULL;

Query 6: Samples with no mutations at all:
SELECT COUNT(*) AS samples_without_mutations FROM samples s LEFT JOIN mutations m ON m.sample_id = s.sample_id WHERE m.mutation_id IS NULL;

Query 7: What is the grain of mutations? Is it one row per sample per gene, or something finer? This finds the sample-gene pairs with the most rows:
SELECT sample_id, gene_symbol, COUNT(*) AS n FROM mutations GROUP BY sample_id, gene_symbol ORDER BY n DESC LIMIT 5;

.quit

- **Verification:** I wrote my predictions (many of which were incorrect by my own logic) and checked them against the commands that Claude sent and their outputs. Claude had the cohort.db file attached to the message.

## Entry 2: First query
- **What I asked (verbatim):** "Can you help me write a command in sqlite3 that counts the protein-altering mutations (non-silent) in the 5 genes for each patient? I also need a command that will show me the number of unique people that have at least one non-silent mutation in any of those 5 genes (each only counting once) and also which specific genes are hit per person (patient can hit once per gene but count multiple times if they have mutations in different genes). This I will calculate the expected rows off of by calculating `patient_gene_pairs` + (566 - `patients_with_hit`). I then need help writing a .sql file that breaks down this information patient by patient and gene by gene." 
- **Exact output (verbatim):**
### Query 1
- **The shape of the result:** SQL will return a *long* table with one row per patient × gene that has at least one mutation, plus one row for each patient with none, so nobody is lost. Python can reshape it to wide format later.

### Control total

Before any joins, count the protein-altering mutations in the five genes straight from `mutations`. **Add up the five numbers and write down the total.** It's your control total, because the counts in the query must add up to it.

```bash
sqlite3 -header -column data/cohort.db "SELECT gene_symbol, COUNT(*) AS n FROM mutations WHERE variant_classification != 'Silent' AND (gene_symbol = 'TP53' OR gene_symbol = 'KRAS' OR gene_symbol = 'EGFR' OR gene_symbol = 'STK11' OR gene_symbol = 'KEAP1') GROUP BY gene_symbol ORDER BY n DESC;"
```
(`!=` means "not equal to.")

### Predict the row count

This counts patients with at least one protein-altering hit, and how many distinct patient-gene pairs exist. The `||` glues two text values together, and `COUNT(DISTINCT ...)` counts each pair once:

```bash
sqlite3 -header -column data/cohort.db "SELECT COUNT(DISTINCT s.patient_id) AS patients_with_hit, COUNT(DISTINCT s.patient_id || '-' || m.gene_symbol) AS patient_gene_pairs FROM mutations m JOIN samples s ON s.sample_id = m.sample_id WHERE m.variant_classification != 'Silent' AND (m.gene_symbol = 'TP53' OR m.gene_symbol = 'KRAS' OR m.gene_symbol = 'EGFR' OR m.gene_symbol = 'STK11' OR m.gene_symbol = 'KEAP1');"
```

Now work out your **expected row count** for the query:

> expected rows = `patient_gene_pairs` + (566 − `patients_with_hit`)

Why: a patient with hits gets one row per gene they have; a patient with no hits gets exactly one row, with the gene blank. Write your number down.

### Write the query into a `.sql` file

The rubric wants queries saved in a `.sql` file so a grader can run them:

```bash
cat > sql/queries.sql <<'EOF'
-- Query 1: protein-altering mutation counts per patient per gene.
-- Grain of the result: one row per patient x gene combination with at least one
--   protein-altering mutation, plus one row (gene = NULL, count = 0) for each
--   patient with none, so all 566 patients stay in the result.
-- Protein-altering = every variant_classification except 'Silent'.
-- Genes: TP53, KRAS, EGFR, STK11, KEAP1.
SELECT p.patient_id,
       m.gene_symbol,
       COUNT(m.mutation_id) AS n_mutations
FROM patients p
LEFT JOIN samples s
  ON s.patient_id = p.patient_id
LEFT JOIN mutations m
  ON m.sample_id = s.sample_id
 AND m.variant_classification != 'Silent'
 AND (m.gene_symbol = 'TP53' OR m.gene_symbol = 'KRAS' OR m.gene_symbol = 'EGFR'
      OR m.gene_symbol = 'STK11' OR m.gene_symbol = 'KEAP1')
GROUP BY p.patient_id, m.gene_symbol
ORDER BY p.patient_id, m.gene_symbol;
EOF
```

### Run it and count the rows

`<` feeds the file into `sqlite3`, and `wc -l` counts output lines (no header in CSV mode, so lines = rows):

```bash
sqlite3 -csv data/cohort.db < sql/queries.sql | wc -l
```

Does it match your expected count? Then peek at the top of the result:

```bash
sqlite3 -header -column data/cohort.db < sql/queries.sql | head -15
```

### Hand-check two patients

First, patient `TCGA-17-Z023` has TP53 mutations including a `Silent` one. Look at the raw rows:

```bash
sqlite3 -header -column data/cohort.db "SELECT s.patient_id, m.gene_symbol, m.variant_classification, m.protein_change FROM samples s JOIN mutations m ON m.sample_id = s.sample_id WHERE s.patient_id = 'TCGA-17-Z023' AND m.gene_symbol = 'TP53';"
```
Then see what the query says for that patient and for `TCGA-64-1678` (a tumor with no mutation calls at all):
```bash
sqlite3 -header -column data/cohort.db < sql/queries.sql | grep -E "TCGA-17-Z023|TCGA-64-1678"
```
Does the query's count for TP53 match what *you* count by hand from the raw rows, with `Silent` excluded? What does the other patient's row look like?

### See the `WHERE` trap with your own eyes

This is the same query with the filters moved from `ON` into `WHERE`. Don't save it. Just compare the row count:

```bash
sqlite3 -csv data/cohort.db "SELECT p.patient_id, m.gene_symbol, COUNT(m.mutation_id) FROM patients p LEFT JOIN samples s ON s.patient_id = p.patient_id LEFT JOIN mutations m ON m.sample_id = s.sample_id WHERE m.variant_classification != 'Silent' AND (m.gene_symbol = 'TP53' OR m.gene_symbol = 'KRAS' OR m.gene_symbol = 'EGFR' OR m.gene_symbol = 'STK11' OR m.gene_symbol = 'KEAP1') GROUP BY p.patient_id, m.gene_symbol;" | wc -l
```
The difference between this number and the count is the number of patients who silently vanished. It's a good thing to cite.

### Check-in

Paste the outputs of plus your expected-row calculation. I'll check them against my own run.
- **Verification:** I ran the first two commands and did my calculations:
    TP53 = 305
    KRAS = 172
    KEAP1 = 103
    EGFR = 85
    STK11 = 81
        Total = 746

    `patients_with_hit` = 457
    `patient_gene_pairs` = 700
        Expected rows = 700 + 566 - 457 = 809
Then I wrote the sql file and ran it. The row count matches my calculations (809). I also ran and compared the `WHERE` version instead of the `ON` version to see the silently dropped 109 patients. The hand checking of patients also checked out. 

## Entry 3: Second query
- **What I asked (verbatim):** "Can you write me another sql query script just like the one above that counts patients per tissue source site per tumor stage? Also, can you write me commands like the others to compute expected row count?"
- **Exact output (verbatim):** 
### Query 2, patients per tissue source site per tumor stage

**Write Query 2:**
```bash
cat > sql/query2_site_stage.sql <<'EOF'
-- Query 2: number of patients per tissue source site per tumor stage.
-- Grain of the result: one row per tissue source site x stage combination that occurs.
-- Starts FROM patients so every patient is counted, including those whose stage is
--   missing (NULL); GROUP BY keeps NULL-stage patients as their own group within a site.
-- COUNT(DISTINCT patient_id) counts each patient once, even if a join ever repeated them.
SELECT s.tissue_source_site,
       p.stage,
       COUNT(DISTINCT p.patient_id) AS n_patients
FROM patients p
LEFT JOIN samples s
  ON s.patient_id = p.patient_id
GROUP BY s.tissue_source_site, p.stage
ORDER BY s.tissue_source_site, p.stage;
EOF
```

**Get an independent expected row count.** This time we compute the expectation a *different way* than `GROUP BY`. List each patient's site and stage as raw lines (one per patient), then let `sort -u` keep only the unique site-stage combinations. The number of lines it leaves is the number of rows Query 2 should return:

```bash
sqlite3 -csv data/cohort.db "SELECT s.tissue_source_site, p.stage FROM patients p JOIN samples s ON s.patient_id = p.patient_id;" | sort -u | wc -l
```
Write that down as your **expected rows**. As a sanity check, the same command without `sort -u |` should print 566, one line per patient:
```bash
sqlite3 -csv data/cohort.db "SELECT s.tissue_source_site, p.stage FROM patients p JOIN samples s ON s.patient_id = p.patient_id;" | wc -l
```

**Run Query 2 and compare:**
```bash
sqlite3 -csv data/cohort.db < sql/query2_site_stage.sql | wc -l
```
```bash
sqlite3 -header -column data/cohort.db < sql/query2_site_stage.sql | head -12
```

**Confirm the missing-stage patients survived.** In CSV output, a blank stage appears as two commas in a row (`,,`), so `grep` can find those rows:
```bash
sqlite3 -csv data/cohort.db < sql/query2_site_stage.sql | grep ',,'
```
Add up the last-column numbers from those rows by hand, then compare with the number of patients whose stage is missing:
```bash
sqlite3 -header -column data/cohort.db "SELECT COUNT(*) AS patients_missing_stage FROM patients WHERE stage IS NULL;"
```
They should be equal. Also note how *few* rows the `grep` returns compared to that patient count, and think about what that says about where the missing stages are.

### Check-in

Paste the outputs.
- **Verification:** I typed out the second sql script Claude generated. Then I ran the two commands to check the expected row counts individually (142 and then 566 without unique) and then ran the `query_2.sql`. The expected rows checked out (both 142). I also verified thath the missing stage patients were kept as Claude suggested:
```bash 
"St Joseph's Medical Center (MD)",,1
"Washington University",,52
"Washington University - Cleveland Clinic",,1
```
```bash
patients_missing_...
--------------------
                  54
```
Which 52 + 1 + 1 checks out. 

## Entry 4: Feature table
- **What I asked verbatim:** I need to build a feature table with one row per patient (566 rows), with columns for: sex, age at diagnosis, stage, tissue source site, tumor mutation burden, and one column per gene from the above protein-altering mutation count. I need to do this by combining SQL (for the querying and joining) with Python (for reshaping into wide format). It cannot be pure SQL pivoting. Can you walk me through and provide scripts with how this can be done?
- **Note:** I did not even know where to start with this step so I needed Claude's help for most of it.
- **Exact output (verbatim):** 

### The Python script, part 1

**The plan.** SQL for the querying and joining, and Python for the reshaping into wide format. We'll use two SQL pieces:

| Piece | Grain (one row is...) | Rows |
|---|---|---|
| **Base table** (new Query 3): sex, age, stage, site, TMB | one patient | 566 |
| **Query 1** (already done): gene counts | one patient × gene (plus patients with no hit) | 809 |

In the next step, Python will reshape Query 1 into one row per patient with a column per gene and attach it to the base table. First we get both pieces loaded and audited.

**Write the base query.** It's a plain `LEFT JOIN` from `patients` to `samples`:
```bash
cat > sql/query3_patient_base.sql <<'EOF'
-- Query 3: one row per patient with the clinical and tumor columns for the feature table.
-- Grain of the result: one row per patient (566).
-- LEFT JOIN from patients keeps every patient even if a sample were missing
--   (none are, but the check is cheap).
SELECT p.patient_id,
       p.sex,
       p.age_at_diagnosis,
       p.stage,
       s.tissue_source_site,
       s.tmb_nonsynonymous
FROM patients p
LEFT JOIN samples s
  ON s.patient_id = p.patient_id
ORDER BY p.patient_id;
EOF
```
**Predict first:** from what you learned about patients and samples, how many rows should this return? Then check:
```bash
sqlite3 -csv data/cohort.db < sql/query3_patient_base.sql | wc -l
```

**Create the script.** It reads each query from its `.sql` file, so the SQL lives in one place and the Python never duplicates it:
```bash
cat > scripts/build_feature_table.py <<'EOF'

import sqlite3

import pandas as pd

DB_PATH = "data/cohort.db"
BASE_SQL = "sql/query3_patient_base.sql"
GENE_COUNTS_SQL = "sql/query1_gene_counts.sql"
GENES = ["TP53", "KRAS", "EGFR", "STK11", "KEAP1"]


def run_sql_file(con, path):
    """Run the query saved in a .sql file and return the result as a DataFrame."""
    with open(path) as f:
        return pd.read_sql(f.read(), con)


def main():
    con = sqlite3.connect(DB_PATH)

    n_patients = con.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
    base = run_sql_file(con, BASE_SQL)
    gene_counts_long = run_sql_file(con, GENE_COUNTS_SQL)
    con.close()

    print("Patients in the patients table:", n_patients)
    print("Rows in base table (query 3):", len(base))
    print("Rows in long gene-count table (query 1):", len(gene_counts_long))
    print("Distinct patients in long gene-count table:", gene_counts_long["patient_id"].nunique())


if __name__ == "__main__":
    main()
EOF
```

What the pieces do:
- **Constants at the top** (`DB_PATH`, the `.sql` paths, `GENES`) mean anything that might change is in one visible place. `GENES` is used in the next step.
- **`run_sql_file`** is a small function that runs a `.sql` file through `pd.read_sql`.
- **`n_patients`** pulls the "before any joins" patient count straight from the source table.

**Run it from the repo root** (your environment should be active):
```bash
python scripts/build_feature_table.py
```
You should see four lines. Before running, predict what each number should be. Two of them you've already computed in earlier steps.

**7e. Add a row to `CHECKS.md`** for the base query (fill the blanks in your editor afterward):
```bash
cat >> CHECKS.md <<'EOF'
| Query 3: patient base table | ___ | ___ | ___ |
EOF
```

### Check-in

Paste the output of `wc -l`** and the four lines, along with the number you predicted for the base query.
- **Verification:** I made my predictions about the numbers that would appear and expected row counts 566, 566, 809, 566. I typed up the third query and the python script. I ran the commands and the numbers checked out:
```bash
Patients in the patients table: 566
Rows in base table (query 3:) 566
Rows in long gene-count table (query 1): 809
Distinct patients in long gene-count table: 566
```
- **What I asked next (verbatim):** I pasted the results (no other context) to Claude and it prompted this:
- **Exact output (verbatim):** 
Everything lines up: 566, 566, 809, 566. Your base query returns one row per patient, your Query 1 result covers all 566 patients, and the 809 matches your earlier expectation.

It works on my side, on pandas 3.0.5 and on your pandas 2.2.3 version.

### Zero vs. missing: the decision behind the script

The two kinds of "nothing" in this data mean different things:

- **A zero** means we looked and found no protein-altering mutation in that gene. It's a real, observed value.
- **An NA** means the value isn't known, as with a missing sex, age, or stage. We never fill those in.

The harder case is the four tumors with no mutation calls at all. Are their gene counts zero or unknown? The database has one clue, so let's check it. **Run this** (it's the same "samples with no mutations" idea as your Query 6, now asking for their tumor mutation burden):
```bash
sqlite3 -header -column data/cohort.db "SELECT s.patient_id, s.tmb_nonsynonymous FROM samples s LEFT JOIN mutations m ON m.sample_id = s.sample_id WHERE m.mutation_id IS NULL;"
```
Look at the TMB values. The decision I recommend, which the script implements:

- **Gene counts:** a patient with no protein-altering mutation in a gene gets **0**, including those four tumors if their TMB agrees.
- **Sex, age, stage:** stay **NA**, never filled.

You'll write the reasoning in your own words in the next step. The code comments hold the short version.

### Reshape, merge, check, and write the TSV

**Replace the script with the full version.** (This also fixes the small typo in a print line: `(query 3:)`.)
```bash
cat > scripts/build_feature_table.py <<'EOF'

import sqlite3

import pandas as pd

DB_PATH = "data/cohort.db"
BASE_SQL = "sql/query3_patient_base.sql"
GENE_COUNTS_SQL = "sql/query1_gene_counts.sql"
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
    Patients with no protein-altering mutation in any of the five genes have no
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
    # protein-altering mutation in these genes, which is a real zero, not "unknown".
    # Clinical columns (sex, age, stage) are NOT filled: they stay NA.
    feature_table[GENE_COLUMNS] = feature_table[GENE_COLUMNS].fillna(0).astype(int)

    # Checks: stop with an error if a join lost, repeated, or invented anything.
    total_long = gene_counts_long["n_mutations"].sum()
    total_wide = feature_table[GENE_COLUMNS].sum().sum()
    assert len(feature_table) == n_patients, "patient count changed after the joins"
    assert feature_table["patient_id"].is_unique, "a patient appears more than once"
    assert total_wide == total_long, "mutation counts changed during the reshape"

    print("Patient count audit")
    print(f"  patients table:           {n_patients}")
    print(f"  after base query:         {len(base)}")
    print(f"  after adding gene counts: {len(feature_table)}")
    print("Mutation count audit (protein-altering, five genes)")
    print(f"  long table total:         {total_long}")
    print(f"  wide table total:         {total_wide}")
    print("Missing values (NA) per column")
    print(feature_table.isna().sum().to_string())

    feature_table.to_csv(OUTPUT_PATH, sep="\t", index=False, na_rep="NA")
    print(f"Wrote {OUTPUT_PATH}: {feature_table.shape[0]} rows x {feature_table.shape[1]} columns")


if __name__ == "__main__":
    main()
EOF
```

**What the new parts do:**
- **`reshape_gene_counts`** turns the long result (809 rows) into wide format with `pivot_table`. `aggfunc="sum"` is there because `pivot_table` otherwise *averages* duplicates. The SQL already fixed the grain to one row per patient-gene, so it's only insurance. Patients with no hit have a blank gene, so they drop out of the pivot. That's expected, and the merge brings them back.
- **`how="left"` merge** keeps all 566 base patients, the same left-join habit as in SQL.
- **`.fillna(0)` is applied only to the five gene columns.** Sex, age, and stage are never touched, which is the rubric's "don't fill in values you made up."
- **The three `assert` lines** are your "show the check" evidence. The script stops with an error if a join loses a patient, repeats one, or changes the mutation total.
- **`na_rep="NA"`** writes missing values as the text `NA`, so they're clearly different from a `0`.

**Run it.** Predict first: which columns should show NA counts, and which should show none?
```bash
python scripts/build_feature_table.py
```

**Inspect the TSV.** The line count should be one more than the number of patients, because of the header:
```bash
head -4 outputs/feature_table.tsv
```
```bash
wc -l outputs/feature_table.tsv
```
Then trace three patients you already know back to your earlier outputs: `TCGA-05-4395` (several genes in your Query 1 output), `TCGA-64-1678` (no mutations), and `TCGA-17-Z023` (the one with a silent TP53 mutation):
```bash
grep -E "TCGA-05-4395|TCGA-64-1678|TCGA-17-Z023" outputs/feature_table.tsv
```
Do the gene counts match what Query 1 and your hand-checks said? What do you notice about the clinical columns for one of these patients?

### Check-in

Paste the output of the TMB query, the other **full output**, and the **three commands**.
- **Verification:** As with the other steps, I ran the commands, checked it against my own predictions made prior (566, 566, 566 and mutation total is 746 before and after the reshape). All 4 tumors without mutation have a tumor mutation burden of 0.0. The 567 lines is the 566 patients plus the header. 

## Entry 5: Data Dictionary Check
-**What I asked (verbatim):** "Can you confirm or write a command that checks the data dictionary I created against the TSV?" (pasted the dictionary)
-**Exact output (verbatim):** 
**Check that the dictionary covers every column**

This loop reads the 11 column names from the first line of your TSV and checks that each one has a row in the dictionary. It prints ok or MISSING for each:

```bash
for c in $(head -1 outputs/feature_table.tsv); do grep -q -F "| \`$c\` |" DATA_DICTIONARY.md && echo "ok      $c" || echo "MISSING $c"; done
```
You should see eleven ok lines. This is the same habit as the row-count checks, applied to documentation: you check it instead of assuming.