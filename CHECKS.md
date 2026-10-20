# Row-count checks

| Query | Expected rows | Got | Explanation |
| --- | --- | --- | --- | 
| Query 1: protein-altering counts per patient per gene | 809 | 809 | Both matched. Using the `WHERE` version of the query silently drops 109 patients if it was used instead of `ON`. | 
| Query 2: counts patients per tissue source site per tumor stage | 142 | 142 | Both matched. |
| Query 3: patient base table | 566, 566, 809, 566 | 566, 566, 809, 566 | All matched. | 