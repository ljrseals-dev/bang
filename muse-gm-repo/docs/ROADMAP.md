# Roadmap and open decisions

## Needs your decision
1. **Penalty terms.** The design notes add penalties (Void_Representation -0.15, Guilt_As_Excuse -0.15, Regret_Generation -0.20) and bonuses (Guilt_Earnedness, Institutional_Density, Guilt_Behavioral_Load). The engine only supports weights that sum to 1. Decide: subtract penalties from the total, or renormalize the whole objective.
2. **Draft-only terms.** Guilt_Earnedness, Regret_Generation, Void_Representation and the Reconstruction Test describe a drafted page, not a configuration choice. Before a script exists they can only be proxied (for example a node x containment institutional-density table). Decide: proxies now, or evaluate them on drafts.
3. **License.** None is included. Pick one (MIT, Apache-2.0, all rights reserved) before publishing.

## Planned work
- New variables as config only: containment_geography (9), survivor_guilt sub-dimensions (loss, agency, public status, carrying behavior), forgiveness_arc/mode/wrong_type, what-if branch, temporal_gap, ghetto_register, implied_reader.
- Staged search: the full composed space exceeds 10^9, so run Stage 1 (spine), keep top-K, then Stage 2 (tonal and guilt/forgiveness), then Stage 3 (structure), exhaustive within each stage.
- Penalty support in `rubric.json` (negative terms with explicit semantics).
- Machine-checkable versions of the refusal conditions (scene tags, narration-vs-action ratio, page-turn checks) applied to saved artifacts.
- Pole C taxonomy of conversion nodes; a language-register module; a music-register dimension; screenplay output templates.
- Streaming replies; persistent session history.
- Run the Claude API path live and record the result.

## Known weak points
- Rankings are fragile to small weight shifts at the level of pressure and media (see `muse-gm sensitivity`). Node, era and economy are firmer.
- The rubric tables favor well-documented nodes; less-saturated nodes (Salvador, Accra, Marseille, Lagos) score lower mostly on documented-anchor plausibility. Revisit them with sourced research.
