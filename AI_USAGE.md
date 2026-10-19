# AI Usage

**Model:** Claude Sonnet 5.5

(Log entries go here: what I asked, what it suggested, what I changed, and how I verified it.)

## Schema exploring
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
