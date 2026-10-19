# Row-count checks

| Query | Expected rows | Got | Explanation |
| --- | --- | --- | --- | 
| Query 1: protein-altering counts per patient per gene | 809 | 809 | Both matched. Using the `WHERE` version of the query silently drops 109 patients if it was used instead of `ON`. | 