# VeriPatch Curated Benchmark

This directory contains eight deliberately small Python/pytest repositories used to measure the full VeriPatch repair loop. Every task has a stable failing baseline and focuses on one reviewable defect category. It is a portfolio benchmark, not SWE-bench and not a substitute for a broad external evaluation.

## Integrity rules

- Task definitions are fixed in `interview_tasks.jsonl`.
- The agent may edit implementation files but `SafeWorkspace` blocks test edits.
- Evaluation copies each source repository to a temporary workspace.
- Each result records the original repository tree SHA-256, source Git SHA, Docker image identity, budgets, model and token categories.
- Scripted runs are runtime validation only. Model-quality reports require a real provider.

## Verify the failing baselines

Run pytest independently in every directory under `cases/` plus `examples/discount_bug`. Each command must exit non-zero for the intended assertion before a model benchmark begins.

## Run the model benchmark

```powershell
.\.venv\Scripts\veripatch.exe eval `
  --tasks benchmarks/interview_tasks.jsonl `
  --output results/deepseek-v4-flash.jsonl `
  --report results/deepseek-v4-flash.md `
  --provider deepseek `
  --runner docker
```

Do not report a resolved rate until Docker and the real provider run have completed.
