# Addendum: what the baseline run found

*Not part of the paper's text. This records the first full run of the instrument (`results/baseline/`, rubric SHA-256 `04c2bcf7dff0051f...`) so the paper's claims about sensitivity and reproducibility can be checked against it.*

## Rank-1 premises under the `master` profile

| Target | Rank-1 premise | Score |
|---|---|---|
| humanized | Harlem / 1940s-50s numbers/labor / policy/numbers / police surveillance / Black press counter-narrative / matriarch-led / ethical rebel loner | 0.9157 |
| dreaded | Kingston JA / 1980s Yardie/garrison / drug corridor / political garrison patronage / state intelligence file / estranged-return / enforcer | 0.9160 |
| pivot | Harlem / 1940s-50s numbers/labor / policy/numbers / police surveillance / state intelligence file / matriarch-led / heir | 0.8981 |

## Sensitivity: the winners are not robust

The paper says a ranking that survives weight shifts is a robust premise, and one that collapses under a five percent nudge was never a ranking. Applying that test to the baseline (`muse-gm sensitivity`, 12 one-at-a-time shifts of 0.05, renormalized):

| Target | Rank-1 changes under | Rank-1 under `equal` profile |
|---|---|---|
| humanized | 1 of 12 shifts | differs |
| dreaded | 4 of 12 shifts | differs |
| pivot | 6 of 12 shifts | differs |

By the paper's own standard, the exact rank-1 premises for dreaded and pivot are fragile. What is stable is the neighborhood: node, era and economy (Harlem 1940s policy/numbers; Kingston 1980s drug corridor) recur at the top, while systemic pressure and media frame trade places. The honest reading is that the instrument is better at identifying robust regions of the space than a single best cell.

## Reproducibility

The test suite re-runs the engine and compares the top five cases per target against `results/baseline/results.jsonl`, so the "same ranking to the sixth decimal" claim is checked on every CI run (Python 3.10 to 3.12, Linux). It has not been tested on other operating systems or NumPy major versions.

## Other limits

- The SPSS syntax export has not been run in SPSS.
- Rubric tables favor well-documented nodes. Salvador, Accra, Marseille and Lagos score lower mostly because their documented-anchor entries are lower, not because they make weaker stories.
