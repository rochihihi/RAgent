# Flash dialogue upgrade — 2026-09-11

## Implemented

- Flash uses Chat Completions tool calls, with JSON fallback for incompatible providers.
- Nonempty one-character messages reach the semantic model.
- The model may ask a specific clarification even when edit permission is clear but the objective is missing.
- Semantic history increased from 8 to 24 messages; default execution budget increased from 4,000 to 16,000 estimated tokens.
- Concise explanations no longer require a fixed result/evidence/verification template.

## Validation

- 151 Studio, provider and follow-up tests passed before the final Flash tool-call change.
- All 30 provider and follow-up tests passed after that change.
- Ruff passed for changed Python files.
- Live `deepseek-v4-flash`: missing numeric reference, missing edit objective, read-only analysis, and specific edit without commands all passed.
- An earlier live run failed parsing a read-only action under JSON-only transport; switching Flash to tool calls addressed the observed failure in the subsequent run.

Run live evaluation with `.venv\Scripts\python.exe scripts/eval_flash_dialogue.py`.
It uses temporary workspaces and the locally configured DeepSeek credential. API calls incur usage.

## Remaining work

This is a first delivery, not a complete architecture replacement or parity claim.
The competing deterministic/model intent policies, persisted pending choices, long-history retrieval,
mechanical final-claim rewriting and multi-file recovery still need work.
Four smoke cases do not establish a reliable success rate; repeated multi-turn task evaluation remains necessary.
