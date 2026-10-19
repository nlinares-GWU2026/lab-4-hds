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