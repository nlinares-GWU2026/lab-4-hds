# Database schema: `cohort.db`
The `cohort.db` is a database built from the TCGA Lung Adenocarcinoma PanCancer Atlas study. It contains 566 patients each with one sample and a total of 200,789 mutations from a genes table of 17,756 genes. 

## Tables

### patients
- **Grain:** One row is one patient.
- **Primary key:** `patient_id`
- **Foreign keys:** none
- **Columns:**
  - `patient_id`: TCGA patient barcode
  - `sex`: male or female
  - `age_at_diagnosis`: age in years when diagnosed
  - `stage`: tumor stage
  - `vital_status`: whether patient was living or deceased at last follow-up
  - `followup_months`: months of follow-up

### samples
- **Grain:** One row is one tumor sample.
- **Primary key:** `sample_id`
- **Foreign keys:** `patient_id` --> `patients`
- **Columns:**
  - `sample_id`: TCGA sample barcode
  - `patient_id`: TCGA patient barcode (linked to `patients` via `patient_id`
  - `tissue_source_site`: the name of the site that collected the tumor samples Indivumed (TSS code)   
  - `tmb_nonsynonymous`: the mutational load/burden
  - `aneuploidy_score`: metric that quantifies the global level of chromosomal instability in the tumor sample (chromosomal arm-level copy-number alterations)
  - `msi_mantis_score`: a numeric MANTIS score of microsatellite instability where a higher value means more instability
 
### mutations
- **Grain:** One row is one somatic mutation in one sample.
- **Primary key:** `mutation_id`
- **Foreign keys:** `sample_id` --> `samples`, `gene_symbol` --> `genes`
- **Columns:**
  - `mutation_id`: unique identifier generated for specific mutation event
  - `sample_id`: TGCA sample barcode
  - `gene_symbol`: standard name of gene where mutation occurred
  - `variant_classification`: functional translational effect of mutation (how the mutations affects the transcript); `Missense_Mutation`, `Silent`, `Nonsense_Mutation`, `Splice_Site`, `Frame_Shift_Del`, `Frame_Shift_Ins`, `In_Frame_Del`, `Translation_Start_Site`, `Nonstop_Mutation`, `In_Frame_Ins`
  - `variant_type`: structural category of DNA modification: SNP, INS, DEL, ONP
  - `protein_change`: HGVsp notation showing what occurred in the protein string 
  - `chromosome`: which chromosome the mutation occurred on
  - `start_pos`: the start position of the mutation coordinates
  - `end_pos`: the end position of the mutation coordinates
  - `t_ref_count`: Tumor Reference Allele Count - the number of sequencing reads at this exact genomic position that matched normal and healthy human reference genome
  - `t_alt_count`: Tumor Alternative Allele Count - the number of sequencing reads that showed the mutated allele

### genes
- **Grain:** One row is one gene.
- **Primary key:** `gene_symbol`
- **Foreign keys:** none
- **Columns:**
  - `gene_symbol`: official alphanumeric abbreviation assigned by the HGNC
  - `entrez_gene_id`: a unique stable integer assigned by the NCBI Entrez system
  - `chromosome`: what chromosome the gene is on

## Relationships

| Relationship | Linking column | Type | What I checked and found |
|---|---|---|---|
| patients to samples | `samples.patient_id` | One-to-one | Query 1: no patient has more than 1 sample. Query 2: 0 samples without a matching patient. Query 3: 0 patients without a sample. |
| samples to mutations | `mutations.sample_id` | One-to-many (0 - many) | Query 4: 0 mutations point to a missing sample. Query 6: 4 samples have no mutations. Query 7: one sample can have many mutation rows.  |
| genes to mutations | `mutations.gene_symbol` | One-to-many | Query 5: 0 mutations point to a gene missing from `genes`. Query 7: TTN appears in many different samples. |
 
## Grain notes
Query 7 showed some samples have many mutation rows in the same gene. If you want mutations per patient per gene you have to select patients and group by mutations per patient per gene. 
