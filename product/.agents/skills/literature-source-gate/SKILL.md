---
name: literature-source-gate
description: 核验、筛选和引用本项目使用的外部学术文献。用户指定文献与自主检索分别处理；不用于纯项目资料问答或非学术工具文档。
---

# Literature Source Gate

Apply the project source policy without confusing user-selected works with literature discovered on the user's behalf. Source authenticity and exact claim matching remain mandatory in both modes.

## Choose the relevant branch

- A user explicitly identifies a work by concrete citation, DOI/PMID/PMCID or supplied article PDF: read [references/designated-sources.md](references/designated-sources.md). This branch does not apply the project's metric gate, restricted-source classification or associated warning to that work.
- 豆包工作 discovers or selects literature, or the user explicitly requests screening against the project gate: read [references/normal-screening.md](references/normal-screening.md) and the complete [references/screening-policy.md](references/screening-policy.md).
- In a mixed task apply each branch to its corresponding works. A topic, author/journal name or candidate list is not designation of a specific work.
- Missing mandatory policy blocks only the dependent literature work. Report its path; do not improvise thresholds or fabricate evidence.

## Shared evidence boundaries

- Follow the user's explicit scope and the project `AGENTS.md` rules. Do not let a user preference waive source authenticity, retraction checks, or claim-to-source matching.
- Treat `CURRENT_STATE` as the authority for project facts, `RESEARCH_QUESTIONS` for questions and priorities, `PROJECT_STORY` for candidate narratives, and `SOL 原生文档` for proposed routes.
- Use journal and citation metrics only for eligibility, ranking, and alerts. Never use them as evidence that an individual article supports a claim.
- Prefer direct experimental and model matching over journal prestige. In normal screening mode, a high-metric but indirect paper cannot replace a lower-metric direct paper; retain the lower-metric direct paper through the documented exception path.

## Task-specific checks

These scientific and project-boundary checks apply in both modes unless a subsection specifically concerns literature discovery or source ranking.

### Prior art and novelty

Identify which elements are already covered by direct precedent, which sources establish that coverage, and what exact material-system-stimulation-readout combination remains. Treat “not found” as a bounded search result, never proof of nonexistence. Do not use “first,” “unique,” “unprecedented,” or equivalents without a sufficiently systematic and explicitly bounded prior-art search.

### RQ and SOL work

Read the target RQ, direct project evidence, and existing SOL routes before using literature to constrain a solution. Keep literature facts, project facts, route assumptions, and proposed experiments distinct. Respect protected `core_route` fields and user-specified model or experimental constraints.

### Project questions

Separate project-recorded facts, information missing from the project, and external literature evidence. If reliable sources do not answer the question, state the search boundary and uncertainty instead of filling the gap by inference.

## Stop rather than overclaim

Stop or narrow the literature-dependent claim when the source identity cannot be verified, the article does not support the claim, the relevant metric cannot be verified and no restricted-source warning is allowed, or a decisive experimental parameter is absent. Report what information would resolve the limitation.
