# Steps Analyzing Missing Data

## Patient Counts Before and After Joins

| Step | Patients |
|---|---|
| `patients` table (before any join) | 566 |
| After the base query (patients LEFT JOIN samples) | 566 |
| After adding the gene counts (final feature table) | 566 |

No patient was lost or duplicated. Every join starts from the `patients` table and uses LEFT JOIN, and the script stops with an error if the patient count changes, if a patient_id repeats, or if the total mutation count (746 protein altering mutations in the 5 genes) differs before and after the reshape. 

## Gaps in the clinical columns (kept as NA)

| Column | Patients missing | What I did | Why |
|---|---|---|---|
| `sex` | 52 | Left as NA | The value was not recorded. Filling it in would invent data. |
| `age_at_diagnosis` | 71 | Left as NA | Same reason. |
| `stage` | 54 | Left as NA | Same reason. |

The LEFT JOINs keep these patients in the table, and the script only fills the five gene count columns, so sex, age, and stage stay missing. In the TSV, they are written as "NA."

## Pattern in Missing Clinical Data

1. First, to analyze the missing data, I used pandas to inspect the data table to find missing data (NaN) and count the zero values across the 5 cancer gene columns. 
```bash
python -c "import pandas as pd; t = pd.read_csv('outputs/feature_table.tsv', sep='\t'); print(t.isna().sum()); print((t[['TP53_count','KRAS_count','EGFR_count','STK11_count','KEAP1_count']] == 0).sum())"
patient_id             0
sex                   52
age_at_diagnosis      71
stage                 54
tissue_source_site     0
tmb_nonsynonymous      0
TP53_count             0
KRAS_count             0
EGFR_count             0
STK11_count            0
KEAP1_count            0
dtype: int64
TP53_count     279
KRAS_count     398
EGFR_count     497
STK11_count    492
KEAP1_count    464
dtype: int64
```
2. Then I used sqlite3 to identify which medical centers or collection sites have missing patient sex data in the db.
```bash
sqlite3 -header -column data/cohort.db "SELECT s.tissue_source_site, COUNT(*) AS n_missing_sex FROM patients p JOIN samples s ON s.patient_id = p.patient_id WHERE p.sex IS NULL GROUP BY s.tissue_source_site;"
 tissue_source_site    n_missing_sex
---------------------  -------------
Washington University             52
```
3. Then with sqlite3, I quered to find how many patients are completely missing all 3 key clinical variables (sex, age_at_diagnosis, and stage).
```bash
sqlite3 -header -column data/cohort.db "SELECT COUNT(*) AS missing_all_three FROM patients WHERE sex IS NULL AND age_at_diagnosis IS NULL AND stage IS NULL;"
missing_all_three
-----------------
               52
```
4. Then, with sqlite3, I queried to count the total number of patients whose tissue samples originated from Washington University.
```bash
sqlite3 -header -column data/cohort.db "SELECT COUNT(*) AS wash_u_patients FROM patients p JOIN samples s ON s.patient_id = p.patient_id WHERE s.tissue_source_site = 'Washington University';"
wash_u_patients
---------------
             52
```
5. After analyzing all 3 numbers, all are 52. So the 52 patients from Washington University were missing 3 clinical values of `sex`, `age_at_diagnosis`, and `stage`. 
6. Then, I queried with sqlite3 to count how many patients outside of Washington Unviersity are missing their clinical age data.
```bash
sqlite3 -header -column data/cohort.db "SELECT COUNT(*) AS age_missing_elsewhere FROM patients p JOIN samples s ON s.patient_id = p.patient_id WHERE p.age_at_diagnosis IS NULL AND s.tissue_source_site != 'Washington University';"
age_missing_elsew...
--------------------
                  19
```
7. I also counted how many patients outside of Washington University were missing their cancer stage data. 
```bash
sqlite3 -header -column data/cohort.db "SELECT COUNT(*) AS stage_missing_elsewhere FROM patients p JOIN samples s ON s.patient_id = p.patient_id WHERE p.stage IS NULL AND s.tissue_source_site != 'Washington University';"
stage_missing_els...
--------------------
                   2
```
**Conclusion:** All three numbers in 2 - 4 are 52, so the 52 Washington University patients are the same 52 patients missing sex, age, and stage. They are every patient from that site. The remaining gaps are small by comparison: 19 more patients are missing age (71 = 52 + 19) and 2 more are missing stage (54 = 52 + 2) which all are from other sites.

**Why it matters for analysis:** The gaps are not random. They come from one collection site, which holds 52 of 566 patients (about 9.2%). An analysis that uses sex, age, or stage and drops rows with NA would remove that whole site, so the remaining patients would not represent the full cohort. This also shows up in query 2, where the missing-stge rows are almost al in the Washington University group. 

## Gene Counts: Zero vs. Missing
- **What 0 means:** It means that the patient's tumor was sequenced and had no protein altering mutation in that gene ("Silent" mutations are not counted). However, it is still a real, observed value.
- **What a NA would have meant:** It would mean we do not know whether the gene was mutated, for example because the tumor was never sequenced. 
- **Which I used, and why:** I used 0 for all 5 gene count columns, and none of them contain NA. Every tumor in the database has a TMB value, so every tumor was sequenced, which means a gene with no mutation rows is a real "none found." Zeros are common: 279 patients (~ 49.3%) have none in TP53, 398 patients (~ 70.3%) in KRAS, 497 patients (~ 88.8%) in EGFR, 492 patients (~ 86.9%) in STK11, and 464 patients (~ 82.2%) in KEAP1. Turning these into NA would hide that most tumors have no mutations in any one gene.
**Four tumors with no mutation calls at all:** (TCGA-64-1678, TCGA-69-8453, TCGA-78-7143, TCGA-86-A4D0) gene counts were all 0 and all have a TMB of 0.0 which agrees with "sequenced and nothing found."
**Limitations:** The database only keeps mutations inside coding sequence or at splice sites (data's SOURCE.md), so a 0 means no protein altering coding mutation was recorded, not that the gene was completely unchaged.
- **Why I did not fill NA in sex, age, or stage:** Those values are unknown, not 0.There is no justified value to put in and replacing them with 0 or an average would be fabricating data. 

## Where to find in code
`scripts/build_feature_table.py` prints the patient mutation counts every time it runs and stops with an error if any check fails. Missing values are written into a TSV as the letters "NA". 
