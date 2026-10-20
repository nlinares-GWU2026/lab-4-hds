# Data Dictionary: `outputs/feature_table.tsv`

One row per patient (566 rows), 11 columns, tab-separated. Missing values are written as the text `NA`.

| Column | Meaning | Units / Values | Source Table | Missing Values |
|---|---|---|---|---|
| `patient_id` | TCGA patient barcode, unique for each patient | Text (example: `TCGA-05-4244`) | `patients` | None missing |
| `sex` | Patient sex | `male` or `female` | `patients` | `NA` if not recorded (52 patients) | 
| `age_at_diagnosis` | Age when the cancer was diagnosed | Years (33 to 38) | `patients` | `NA` if not recorded (71 patients) | 
| `stage` | Tumor stage at diagnosis | `I`, `IA`, `II`, `IIA`, `IIB`, `IIIA`, `IIIB`, `IV` | `patients` |  `NA` if not recorded (54 patients) |
| `tissue_source_site` | Institution that collected the tumor sample | Text, 34 different sites (example: `Indivumed`) | `samples` | None missing | 
| `tmb_nonsynonymous` | Tumor Mutation Burden (TMB): how many nonsynonymous mutations the tumor has | Mutations per megabase (0 to 69.5) | `samples` | None missing |
| `TP53_count` | Number of protein-altering mutations in TP53 in the patient's tumor | Count (whole number, 0 or more) | `mutations` (joined through `samples`) | Never `NA`. 0 means no protein-altering mutations found  | 
| `KRAS_count` | Same, for KRAS | Count (0 or more) | `mutations` (joined through `samples`) | Never `NA`. 0 means no protein-altering mutations found |
| `EGFR_count` | Same, for EGFR | Count (0 or more) | `mutations` (joined through `samples`) | Never `NA`; 0 means none found |
| `STK11_count` | Same, for STK11 | Count (0 or more) | `mutations` (joined through `samples`) | Never `NA`; 0 means none found |
| `KEAP1_count` | Same, for KEAP1 | Count (0 or more) | `mutations` (joined through `samples`) | Never `NA`; 0 means none found |

## What the Gene Count Columns Count
- **Counted:** every mutation whose `variant_classification` is anything other than `Silent`.
- **Excluded:** `Silent` mutations, which change the DNA but not the protein.
- Each row of the `mutations` table counts once, so a patient with two missense mutations in the same gene has a count of 2. 
- A count of 0 means the tumor was sequenced and no protein-altering mutations was recorded in that gene. See `MISSING_DATA.md` for why 0 is used and not `NA`.
