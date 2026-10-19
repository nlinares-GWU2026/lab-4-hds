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