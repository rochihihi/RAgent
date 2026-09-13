# DeepSeek V4 Flash — Curated Benchmark Report

> This is one real-model run of VeriPatch's eight-task curated repository benchmark, not SWE-bench.

## Result

- Date: 2026-08-28 (Asia/Shanghai)
- Provider / model: DeepSeek / `deepseek-v4-flash`
- Runner: read-only, network-disabled Docker sandbox
- Tasks: 8
- Resolved: 8
- Resolved rate: 100.0%
- Average Agent steps: 4.38
- Average duration: 11.57 seconds
- Input / cached-input / output / reasoning Tokens: 78,969 / 27,008 / 6,454 / 3,831
- Failure counts: none

| Task | Category | Result | Steps | Duration |
|---|---|---:|---:|---:|
| discount-percentage | arithmetic | resolved | 4 | 10.30s |
| pagination-offset | boundary | resolved | 5 | 11.14s |
| localized-cache-key | cache | resolved | 4 | 9.69s |
| boolean-parser | parsing | resolved | 5 | 15.38s |
| inventory-boundary | state | resolved | 3 | 8.68s |
| exception-scope | exceptions | resolved | 4 | 9.13s |
| retry-backoff | sequence | resolved | 4 | 12.43s |
| multi-file-surcharge | multi-file | resolved | 6 | 15.83s |

## Reproducibility

- Source Git SHA: `f076b2fa97ddefd56e9fbba5e95124f8f0743b82`
- Docker image: `veripatch-sandbox:latest`
- Docker image ID: `sha256:725719b0aae14273c1446c1e0e2539cb6ce982e4fc83380c3dd08dc179fdb7b2`

| Task | Repository tree SHA-256 |
|---|---|
| discount-percentage | `8988c4cb2ae8b1453e786867f878dc909057ecd7a1ea383d3b1449c05c37bbaf` |
| pagination-offset | `5a621367b130dfb7a084d4781d615f1f86d6eab206ea0adebf08c10f860b78b6` |
| localized-cache-key | `76e4cce731bafb36df3c011a7f19a9f3fc704caf21e3f1835284b10e67cfa623` |
| boolean-parser | `44f01aac3487ad18796ba1970c528d23dc86bd2511f3a31d4d03cbdb57889cde` |
| inventory-boundary | `0ffd94ca6ad163865bd5ab9a9538092763762cf6c770d335fb1ae255a952b28b` |
| exception-scope | `887d5ce3acfc2b77922fcd2d1bd03c0a672a5a70f62ee2d3a34ca7507541e80d` |
| retry-backoff | `f78a6241d442db6771d368fe05caf03a7b7ef6425c1e951f26bd1160b6a4ab21` |
| multi-file-surcharge | `4319c74a121ee78984f9e5d81ec56f41eba72bcec935ba999893aba93c6dcc02` |

The generated per-task JSONL remains a local evaluation artifact because it contains run IDs and machine-specific execution data. This checked-in report intentionally excludes API credentials and personal account balances.
