-- Query 3: one row per patient with the clinical and tumor columns for the feature table.
-- Grain of the result: one row per patient (566).
-- LEFT JOIN from patients keeps every patient even if a sample were missing
--   (none are, but the check is easy).
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