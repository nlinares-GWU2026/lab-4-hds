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

## Entry 4: 