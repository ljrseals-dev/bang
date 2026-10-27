# The mathematics of MUSE-GM

Everything below is implemented in `muse_gm/engine.py`; the numbers are generated from `muse_gm/data/*.json` and checked by the tests.

## 1. The space

Let the story space be the full factorial of eight nominal variables $V_1,\dots,V_8$ with $n_i$ levels each:

| i | variable | $n_i$ |
|---|---|---|
| 1 | `node` | 14 |
| 2 | `era` | 8 |
| 3 | `economy` | 9 |
| 4 | `pressure` | 7 |
| 5 | `media` | 5 |
| 6 | `family` | 6 |
| 7 | `archetype` | 7 |
| 8 | `effect` | 3 |

$$N=\prod_{i=1}^{8} n_i = 14 \times 8 \times 9 \times 7 \times 5 \times 6 \times 7 \times 3 = 4,445,280$$

A *case* is a vector $x=(x_1,\dots,x_8)$ with $x_i\in\{1,\dots,n_i\}$. The program enumerates all $N$ cases; it never samples. The hard cap is $N\le 10^{9}$ (the run stops with `CONFIG ERROR` above it). Memory is about $8\ \text{arrays}\times 8\ \text{bytes}=64$ bytes per case.

## 2. Lookup tables

A rubric table $T_j$ is a function of a subset of the variables (its *axes*) taking values in $[0,1]$. The rubric contains 24 tables. Examples: `node_era` $=T(x_{node},x_{era})$, `archetype_effect` $=T(x_{archetype},x_{effect})$. A table is broadcast onto the full space, so $T_j(x)$ is defined for every case. Validation requires every entry to be finite and in $[0,1]$ and the array shape to match its axes.

## 3. Components

Six components $C_k(x)\in[0,1]$ are built from tables with term weights $w_{kj}\ge 0$, $\sum_j w_{kj}=1$.

- `linear`: $C_k(x)=\sum_j w_{kj}\,T_j(x)$
- `geomean`: $C_k(x)=\prod_j T_j(x)^{w_{kj}}$ (a weighted geometric mean, so one implausible factor pulls the whole score down)

**Causal_Chain_Integrity** (`geomean`)

$$C(x)=\text{node_era}^{0.22} \cdot \text{node_economy}^{0.18} \cdot \text{era_economy}^{0.15} \cdot \text{node_pressure}^{0.1} \cdot \text{era_pressure}^{0.1} \cdot \text{era_media}^{0.1} \cdot \text{node_media}^{0.15}$$

**Empathy_Structure** (`linear`)

$$C(x)=0.6\,\text{archetype_effect} + 0.2\,\text{media_effect} + 0.2\,\text{family_effect}$$

**Family_System_Realism** (`linear`)

$$C(x)=0.5\,\text{node_family} + 0.25\,\text{era_family} + 0.25\,\text{economy_family}$$

**Manga_Craft_Fidelity** (`linear`)

$$C(x)=0.25\,\text{economy_craft} + 0.25\,\text{era_craft} + 0.25\,\text{archetype_craft} + 0.25\,\text{media_craft}$$

**Dread_Enforcement_Potential** (`linear`)

$$C(x)=0.4\,\text{archetype_dread} + 0.3\,\text{pressure_dread} + 0.3\,\text{media_dread}$$

**Counter_Stereotypical_Power** (`linear`)

$$C(x)=0.25\,\text{media_counter} + 0.25\,\text{pressure_counter} + 0.25\,\text{archetype_counter} + 0.25\,\text{node_specificity}$$

## 4. Objective

A weight profile $\lambda=(\lambda_1,\dots,\lambda_6)$ with $\lambda_k\ge0$ and $\sum_k\lambda_k=1$ (checked to $10^{-8}$) gives the score

$$S_\lambda(x)=\sum_{k=1}^{6}\lambda_k\,C_k(x)\in[0,1]$$

| component | `master` | `equal` |
|---|---|---|
| Causal_Chain_Integrity | 0.3 | 0.166667 |
| Empathy_Structure | 0.2 | 0.166667 |
| Family_System_Realism | 0.15 | 0.166667 |
| Manga_Craft_Fidelity | 0.15 | 0.166667 |
| Dread_Enforcement_Potential | 0.1 | 0.166667 |
| Counter_Stereotypical_Power | 0.1 | 0.166667 |

`master` is Module 2 of the Master Prompt. A non-finite score raises an error (fail closed).

## 5. Ranking

For an effect target $e$, the program ranks the $N/3$ cases with $x_{effect}=e$ by $S_\lambda$ descending. Ties are broken by ascending flat array index, so the order is deterministic. The number of cases within $10^{-12}$ of the top score is reported as `tied_at_first`.

`--distinct v_1,v_2,\dots` collapses the list to cores: for each combination $c$ of the named variables, $\;S^{*}(c)=\max_{x\supseteq c}S_\lambda(x)$, then ranks cores by $S^{*}$ and reports the argmax case for each.

`--select` restricts the space to a product of chosen levels $\prod_i L_i$ before scoring; ranking is then exhaustive over that subspace, and the manifest records the selection and the full-space size.

## 6. Sensitivity

For a base profile $\lambda$ and each component $k$ and sign $s\in\{+1,-1\}$, the shifted profile is

$$\lambda'_k=\max(0,\lambda_k+s\delta),\qquad \lambda'_j=\lambda_j\ (j\ne k),\qquad \tilde\lambda=\lambda'/\textstyle\sum_j\lambda'_j,\qquad \delta=0.05,$$

giving 12 variants. The report lists which variants change the rank-1 case, and the overlap of the top-$k$ set with a second profile.

## 7. Worked example (generated)

**humanized** — Harlem | 1940s-50s numbers/labor | policy/numbers | police surveillance | Black press counter-narrative | matriarch-led | ethical rebel loner

$$S=0.3\times0.9895 + 0.2\times0.9400 + 0.15\times0.9750 + 0.15\times0.9375 + 0.1\times0.6150 + 0.1\times0.8250=0.9157$$

(components rounded to 4 decimals; stored score is computed from unrounded values)

**dreaded** — Kingston JA | 1980s Yardie/garrison | drug corridor | political garrison patronage | state intelligence file | estranged-return | enforcer

$$S=0.3\times0.9895 + 0.2\times0.9100 + 0.15\times0.9250 + 0.15\times0.8625 + 0.1\times0.9400 + 0.1\times0.7500=0.9160$$

(components rounded to 4 decimals; stored score is computed from unrounded values)

**pivot** — Harlem | 1940s-50s numbers/labor | policy/numbers | police surveillance | state intelligence file | matriarch-led | heir

$$S=0.3\times0.9548 + 0.2\times0.8650 + 0.15\times0.9750 + 0.15\times0.9125 + 0.1\times0.8050 + 0.1\times0.7500=0.8981$$

(components rounded to 4 decimals; stored score is computed from unrounded values)

## 8. What the numbers are

Every table entry is an encoded editorial judgment. The mathematics is exact; the inputs are not measurements. Manifests carry `evidence_status: rubric_encoded_judgments_not_measured_data` and the SHA-256 of both configuration files, so any change to a table changes the hash.
