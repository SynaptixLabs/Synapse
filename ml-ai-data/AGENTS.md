# ml-ai-data/ — AGENTS.md (Tier-2)

> Domain-local rules for ML / AI / data work (ingestion, transforms, features, training, eval,
> inference services). Inherits the root [`../AGENTS.md`](../AGENTS.md) and the canonical brain
> [`../.claude/`](../.claude/00_INDEX.md). Keep this thin. *(Delete this directory if your project
> has no ML/data surface.)*

**Scope:** data pipelines, feature engineering, model training/eval, and inference endpoints. Owner
class: `dev` (CORE); add a specialized class if the work warrants it.

## Local rules

- **Reproducibility is the acceptance bar.** A result isn't done until it can be re-run from
  versioned data + code + config and produces the same numbers. That's this domain's "evidence,
  not assertion" (Commandment B1).
- **No real/PII data in the repo or in tests** without an explicit, flagged decision — use
  synthetic fixtures. Real data egress is a one-way door → escalate to `cpto`/founder.
- **Reuse-first** for datasets, features, and eval harnesses: check
  `../project-management/03_MODULE_CONTRACTS.md` before creating a parallel pipeline.
- Metrics reported are **observed**, never inferred — cite the run that produced them.

<!-- CUSTOMIZE: frameworks, data stores, experiment tracking, model registry. -->
