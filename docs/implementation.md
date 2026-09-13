# VeriPatch Implementation Design

## Objective

实现一个可验证、可恢复、可评测的仓库级软件修复 Agent。系统以客观测试结果为成功门禁，并保存每一步状态、工具调用和成本信息。

## Architecture

```text
Issue + repository + failing test
              |
              v
      baseline reproduction
              |
              v
 AST index + lexical search
              |
              v
  stateful Agent controller <---- checkpoint/event store
      |       |       |
   search    edit    test
      |       |       |
      +-------+-------+
              |
              v
 deterministic verification gate
              |
              v
 patch + evidence + trajectory + metrics
```

## Files and Responsibilities

| File | Responsibility |
|---|---|
| `src/veripatch/config.py` | Environment-backed runtime configuration. |
| `src/veripatch/domain.py` | Typed issue, action, observation, state and result models. |
| `src/veripatch/indexing.py` | Python AST symbol index and symbol-aware lookup. |
| `src/veripatch/workspace.py` | Path containment, lexical search, bounded reads and atomic edits. |
| `src/veripatch/testing.py` | Allowlisted pytest runner with timeout and sanitized environment. |
| `src/veripatch/store.py` | SQLite event log and checkpoint persistence. |
| `src/veripatch/models/base.py` | Model protocol and prompt context. |
| `src/veripatch/models/scripted.py` | Offline deterministic demonstration model. |
| `src/veripatch/models/openai.py` | OpenAI Responses API structured-output adapter. |
| `src/veripatch/agent.py` | Explicit repair state machine and verification gates. |
| `src/veripatch/evaluation.py` | Reproducible task runner and aggregate metrics. |
| `src/veripatch/api.py` | FastAPI endpoints for runs and trajectories. |
| `src/veripatch/cli.py` | Demo, run, inspect and serve commands. |
| `examples/discount_bug/` | Frozen Python bug used for offline end-to-end verification. |
| `tests/` | Unit, security and end-to-end tests. |

## Iteration 1 — Runtime reliability

### Recoverable execution

- `AgentRunState` persists pre-edit file snapshots and the last action fingerprint window.
- `VeriPatchAgent.resume(run_id)` reloads the checkpoint, reconciles any durable edit transaction, rejects workspace drift, rebuilds the symbol index and continues from `state.step + 1`. It reruns the baseline only when no baseline observation was committed.
- Terminal runs cannot be resumed. Missing repositories and exhausted budgets fail explicitly.
- Multi-file edits are transactional across process crashes: before/after contents and hashes are persisted before writes; write failures roll back and resume reconciles prepared, written and mixed states.

### Test runner abstraction

- `TestRunner` is a protocol returning `TestOutcome`.
- `LocalPytestRunner` remains available for the frozen demo and unit tests.
- `DockerPytestRunner` runs with network disabled, read-only container root and repository bind mount, bounded CPU, memory and PIDs, dropped capabilities and no-new-privileges.
- CLI/API select `docker` for external repositories and explicitly opt into `local` for the offline demo.

### API and trace viewer

- Run creation returns a run identifier immediately and executes in an in-process background task.
- Status, events and result/diff are separate read endpoints.
- The dependency-free Studio renders conversations, audited actions, tests and colorized file changes.
- The API binds to localhost by default and does not claim multi-process durability for its background scheduler.

### Evaluation semantics

- Evaluation records include runner, provider, benchmark kind and runtime/model distinction.
- Scripted demo results are labeled `runtime_validation`; they are never reported as model quality.
- Real model benchmarks require an API key and produce the same JSONL metric schema.

### Delivery artifacts

- Root Dockerfile and Compose run the local API as an unprivileged user.
- GitHub Actions runs Ruff and pytest with coverage.
- `docs/threat_model.md` documents trust boundaries, mitigations and residual risks.
- README includes architecture, setup, demo, API, evaluation, failure modes and resume workflow.

## Core Contracts

### Agent model

`AgentModel.decide(context: ModelContext) -> AgentDecision`

The model returns exactly one typed action. It never receives an unrestricted shell tool.

### Safe workspace

- Every path is resolved and checked to remain under the target repository.
- Reads are line- and size-bounded.
- Edits use exact old-text replacement and fail on zero or multiple matches.
- Test files and protected repository metadata are not editable by default.
- Each edit is written atomically and recorded as a unified diff.

### Test runner

- Accepts argument arrays rather than shell strings.
- Only `pytest` or `python -m pytest` commands are accepted.
- Applies a timeout and removes common secret-bearing environment variables.
- Captures stdout, stderr, duration and exit status.
- External repositories use the Docker implementation by default; local execution is an explicit development/demo mode.

### State machine

```text
created -> reproducing -> investigating -> editing -> verifying
    |           |             |             |          |
    +-----------+-------------+-------------+----------+
                              |                        |
                            failed                 succeeded
```

The run stops on test success, explicit failure, repeated action, step budget, or timeout.

An interrupted non-terminal run resumes from its persisted step. Resume reconciles durable edits and repeats baseline reproduction only when baseline evidence was not committed before the crash.

## Evaluation

Initial metrics:

- issue resolved rate;
- fail-to-pass and pass-to-pass test status;
- valid edit rate;
- average steps, latency and model usage;
- unsafe path/edit rejection rate;
- checkpoint availability.

Baselines and public task ingestion are extension points. The MVP must first pass the included frozen task without network access.

## Acceptance Criteria

- `python -m pytest` passes.
- `veripatch demo` reproduces the bug, edits source code, passes tests and persists a trajectory.
- Path traversal and test-tampering attempts are rejected.
- A run can be inspected from SQLite after completion.
- API health and run-inspection endpoints work without an API key.
- `resume(run_id)` continues a non-terminal checkpoint and rejects terminal runs.
- Docker command construction enforces no network, resource limits and repository-only mounting.
- Statement coverage is at least 90% for the final local test suite.

## Iteration 2 — Runtime and API delivery

### Durable edit transactions

- `AgentRunState` records a prepared edit transaction before repository files are changed.
- A prepared transaction contains the exact edits plus before/after hashes and can be reconciled on resume.
- Resume handles all-before, all-after and mixed transaction states; unknown file drift fails without overwriting user changes.
- SQLite uses WAL and a busy timeout. State plus its corresponding lifecycle event can be committed in one transaction.

### Provider and credential boundary

- `AgentModel.decide(ModelContext) -> ModelReply` remains the provider-neutral contract.
- OpenAI uses Responses structured parsing with `gpt-5.6-terra` and medium reasoning by default.
- DeepSeek defaults to `deepseek-v4-flash`; Flash uses Responses JSON Schema and Pro uses Chat Completions JSON Output.
- Provider responses are always validated as `AgentDecision`; empty or invalid DeepSeek output receives at most one retry.
- Credentials resolve from environment variables first, Credential Manager second and a Windows DPAPI user-encrypted vault third. Plaintext is never persisted in run state, events, benchmark output or logs.
- The localhost GUI may add or remove encrypted credentials through secret-free endpoints; writes are read back before success, `SecretStr` input is never echoed, environment-managed credentials cannot be deleted from the GUI, and task creation gates on provider readiness.
- DeepSeek quota status uses `/user/balance`, a configurable low-balance threshold and a 60-second browser refresh. OpenAI standard keys explicitly report remaining-credit monitoring as unsupported.

### Budgets and metrics

- Runs stop explicitly when step, model-call, input-token or output-token budgets are exhausted.
- `ModelReply`, run state and evaluation output track actual model, request identifier, cached input tokens and reasoning tokens.
- Evaluation records include task tree hash, model, reasoning, configured budgets and failure category.

### Local product surface

- The responsive GUI provides a task wizard, native repository-folder picker with manual path fallback, secure API configuration Sheet, provider readiness, quota status, aggregate metrics, run filters and recent task cards without external frontend dependencies.
- The one-click offline Demo creates a unique copied workspace and redirects to the live trace; the original example remains immutable.
- Runs and events use bounded cursor/offset pagination; public responses exclude source snapshots, edit transactions and action fingerprints.
- The Studio trace separates decisions, tools, tests, failures and colorized Diff instead of rendering an undifferentiated dump.

### Curated benchmark and delivery

- Eight frozen Python/pytest tasks cover arithmetic boundaries, cache keys, parsing, state mutation, exception behavior and multi-file configuration.
- Scripted results remain `runtime_validation`; DeepSeek results are `model_benchmark` with a generated Markdown report.
- Final gates are 90% statement coverage, Ruff, Ruff format, mypy, wheel build/install, offline demo, Docker integration and API smoke tests.
- The completed source is committed to a private GitHub repository after generated data and credentials are excluded.
