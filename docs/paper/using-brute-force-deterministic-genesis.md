# Using Brute Force: Deterministic Genesis of the Origins of Gangsters

**Lewis James Seals Jr. and Laila Star Seals**

---

Most story engines are slot machines. You pull the lever, a premise falls out, you pull again, and a different premise falls out, and you have no way to prove the second one is better than the first or that the thousandth is different from the tenth. Procedural generation has spent forty years producing novelty and calling it invention. Novelty is cheap. What is expensive is knowing the shape of the space you are writing inside.

This paper describes an instrument that does not sample. It enumerates. Every combination of every declared variable is scored, ranked, and written to disk with a hash. Nothing is drawn from a distribution because nothing is drawn at all.

## The problem with sampling

A generative model that samples is a black box with a temperature knob. Ask it for a gangster origin story and it returns the modal answer, which is to say the answer everyone else already got. Ask it for ten thousand and you receive ten thousand variations on the same three neighborhoods. The model has not explored the space; it has memorized its center of mass. Worse, the output is not auditable. You cannot ask why this premise and not another, because there is no "another." There is only the sample you happened to receive.

Determinism fixes the epistemology before it fixes the prose. If the space is finite and declared, then "best" becomes a computable predicate rather than a matter of taste, and taste becomes an explicit input rather than a hidden one.

## The stratagem: a full factorial of origin

The instrument treats a gangster's origin as an eight-factor factorial design. Each factor is a nominal variable with declared value labels, exactly as an SPSS Variable View would carry them:

- **Diaspora node (14):** US South→North migration, Harlem, Chicago, Detroit, South Central LA, Kingston, London, Lagos, Accra, São Paulo, Salvador da Bahia, Port-au-Prince, Marseille, Toronto
- **Era (8):** 1910s–20s Prohibition through the 2000s transnational/digital present
- **Economy (9):** bootlegging, policy, protection, labor racketeering, drug corridor, extortion/militia, fraud, smuggling, informal security
- **Systemic pressure (7):** redlining, police surveillance, garrison patronage, extralegal violence, immigration law, media criminalization, class fracture
- **Media frame (5):** hostile tabloid, Black press counter-narrative, courtroom transcript, oral history, state intelligence file
- **Family system (6):** matriarch-led, sibling split, migration-separated, chosen family, dynastic, estranged-return
- **Archetype (7):** ethical rebel loner, strategist, enforcer, diplomat, self-defense figure, informant, heir
- **Effect target (3):** humanized, dreaded, pivot

Fourteen times eight times nine times seven times five times six times seven times three. The product is 4,445,280. That is the entire space of origins under this vocabulary, and the instrument visits all of it.

## The variable view as authoring surface

The design borrows its interface from survey research rather than from fiction software, and the borrowing is deliberate. A writer who has never opened a statistics package can still read a Variable View: name, label, type, values. Declaring the story world this way does two things that prose cannot. It makes the vocabulary finite and inspectable, and it makes every choice revisable in one place. Change the value labels and you have changed the world. The scoring code does not move.

The instrument exports SPSS syntax, complete with VARIABLE LABELS and VALUE LABELS, alongside a numeric-coded CSV and a labeled twin. A premise is therefore a row, and a row is a case, and the whole corpus of origins can be cross-tabulated by anyone who has ever run a frequency table.

## Twenty-four tables and an honest rubric

Plausibility is encoded as twenty-four two-dimensional tables: node by era, node by economy, era by pressure, archetype by effect target, and so on. These are combined into six named components: Causal Chain Integrity, Empathy Structure, Family System Realism, Manga Craft Fidelity, Dread Enforcement Potential, and Counter-Stereotypical Power. Two weight profiles ship with the instrument, one master and one equal, and the gap between them is itself a finding.

Here is where the paper earns its keep. The tables are not measured data. They are encoded editorial judgments, every one of them, and the instrument's manifest says so in a machine-readable field: `rubric_encoded_judgments_not_measured_data`. That string is not a disclaimer bolted on for lawyers. It is the design. A system that ranks four million premises by human judgment is useful precisely because the judgment is exposed, versioned, and hashed rather than buried in a model's weights. You can disagree with the tables. You can rewrite them and re-run. You cannot do that to a checkpoint.

## Determinism is the product

Every run writes a manifest: the canonical hash of the variables file, the canonical hash of the rubric, the exact command, the profile, the weights, the Python and NumPy versions, the platform, the git commit, and the number of combinations tied at first place. Two researchers on two machines can reproduce the same ranking to the sixth decimal or discover precisely where they diverge.

The scoring path uses a geometric mean on the causal component and linear combinations elsewhere, and it fails closed. Non-finite scores raise. Weights that do not sum to one raise. A table whose shape disagrees with its declared axes raises. The instrument refuses to produce a number it cannot defend.

## Sensitivity as a first-class output

Because the rubric is explicit, the instrument can interrogate it. A sensitivity command compares the master profile against the equal profile, reports top-k overlap, and then perturbs each component weight by five percent in both directions to record whether the winning premise changes. A ranking that survives weight shifts is a robust premise. A ranking that collapses under a five percent nudge was never a ranking; it was an accident of arithmetic.

## What this is not

It is not a claim about audiences. It is not a measurement of authenticity. It does not know whether a script will be good, and it does not pretend that a high-scoring premise writes itself. What it knows is the shape of a declared space and the consequences of a declared taste. The prose is still the author's job.

## The close

Writers have always worked inside a factorial they could not see. This instrument draws the factorial, scores every cell, and hands back the map with its own assumptions printed on the back. Brute force is not the opposite of craft. Applied to the whole space at once, it is craft made legible.
