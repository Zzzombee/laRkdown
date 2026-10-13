# Normal source screening

First read [screening-policy.md](screening-policy.md) completely; it owns thresholds, source eligibility, discovery/retry rules, exceptions, warnings and citation display. Reuse it within the task unless it changes.

The numbered workflow below applies only to normal screening mode.

### 1. Define the claim and source role

Before searching, state what the source must support and classify its role:

- core experimental, causal, mechanistic, safety, or novelty evidence;
- supporting background or plausibility;
- method, definition, guideline, or consensus;
- conflicting, negative, historical, or risk evidence.

Do not use a background review as if it were the direct experiment, or a method paper as evidence that the project's mechanism is established.

### 2. Discover candidates within the declared scope

Record the search date, time window, databases, material or device, biological system, stimulation, readout, and follow-up window. Apply any workflow-specific time window in `AGENTS.md`, such as the default five-year window for an RQ solution.

Use the discovery and retry policy in [screening-policy.md](screening-policy.md). Discovery metadata alone is not verification.

### 3. Verify each consequential source

For every source that materially affects a conclusion, experimental decision, solution route, or novelty claim:

1. verify title, authorship, year, article type, journal, and DOI or stable publisher identifier;
2. check retraction, withdrawal, expression-of-concern, correction, and source-integrity status;
3. inspect the original article, authoritative full text, journal page, PubMed/PMC record, or DOI page;
4. confirm that the reported experiment and result support the exact sentence being written;
5. distinguish results from the authors' discussion, interpretation, and speculation.

### 4. Build a match record

For each key paper, record the material, species or system, disease model, brain region or circuit, stimulation modality and timing, readout, follow-up, source role, and directness. Mark missing fields as unknown; never infer them from adjacent papers.

### 5. Apply the source gate

Classify each source using [screening-policy.md](screening-policy.md):

- **excluded**: cannot serve as positive evidence;
- **preferred**: passes integrity, claim matching, and the default metric gate;
- **restricted**: scientifically relevant but below or unverified against the default metric or citation-age gate.

Replace a restricted source when a preferred source supports the same claim equally directly. Retain it only when an allowed exception is documented, the claim cannot be preserved without it, and the required warning accompanies the output.

### 6. Calibrate the claim

Label support as direct, indirect, plausibility-only, conflicting, or speculative. State what the source supports and what it cannot support. Do not assemble different materials, cells, species, brain regions, stimulation conditions, or readouts into a mechanism described as directly demonstrated.

### 7. Render citations and warnings

In user-facing documents and dialogue, use the citation format and restricted-source warning in [screening-policy.md](screening-policy.md) and put citations next to the claims they support. In internal skill, policy, configuration, or working files, keep paths, identifiers, DOIs, and URLs literal rather than wrapping them in display-layer links. Do not hide a restricted-source warning in an unrelated appendix or omit it from a publication-ready handoff.

### 8. Audit before delivery

Confirm that:

- every external citation exists and resolves to the intended work;
- every consequential claim has an appropriately matched source;
- all metric values include their metric source, edition or category where relevant, and query date;
- all restricted sources have an allowed reason, bounded claim, corroboration status, and visible warning;
- excluded sources are absent from positive evidence;
- no novelty or absence statement exceeds the recorded search scope.
