# Architecture

## System Flow

```text
Issue + frozen repository + pytest command
                     |
                     v
            baseline reproduction
                     |
                     v
          AST index + lexical search
                     |
                     v
       typed AgentDecision state machine
          |          |           |
       search       exact edit   test
          |          |           |
          +----------+-----------+
                     |
                     v
        deterministic verification gate
                     |
                     v
     patch + events + checkpoint + metrics
```

## Trust Boundaries

The model never receives a raw shell tool. It returns one Pydantic-validated action. Repository paths pass through `SafeWorkspace`, edits require an exact single match, and tests use an immutable pytest command selected by the caller. External repositories should use `DockerPytestRunner`; the local runner exists for development and the frozen offline demo.

## Recovery

State-changing events and checkpoints are committed atomically in SQLite WAL mode. Before any filesystem write, the controller persists a transaction containing exact before/after contents and hashes. `resume(run_id)` reconciles not-written, fully-written and partially-written transactions, rejects unknown workspace drift, and reruns the baseline only when the crash happened before baseline evidence was recorded.

## Provider Boundary

OpenAI and DeepSeek implement the same `AgentModel.decide(ModelContext) -> ModelReply` contract. OpenAI uses typed Responses output; DeepSeek V4 Flash uses Responses JSON Schema and V4 Pro uses Chat Completions JSON Output. Provider request IDs remain internal, while token categories and the actual model name are recorded as metrics. Credentials come from environment variables or Windows user-scoped encrypted storage: Credential Manager first, with a DPAPI-encrypted vault fallback for service contexts where WinVault has no active logon session.

DeepSeek quota monitoring calls the provider balance endpoint on demand and returns a typed, secret-free snapshot. The browser refreshes it every 60 seconds and the CLI exposes the same query. Balance responses are not written to checkpoints or events. OpenAI standard keys are marked unsupported for remaining-credit queries because its organization Usage/Costs APIs require admin credentials and describe spend rather than available credit.

## Verification

A run can succeed only after a non-empty patch and a zero-exit deterministic test. Model-written summaries, reviewer opinions and scripted demo output are not verification signals. Scripted results are labeled `runtime_validation`; only real provider runs may be labeled `model_benchmark`.

## Deployment Boundary

The FastAPI background scheduler is intentionally single-process and local-first. It supports local use and interactive demonstrations, not distributed job scheduling. A production deployment would replace in-process tasks with an authenticated queue and per-run isolated workers while retaining the same state and event contracts.

The dependency-free responsive GUI is rendered by `studio_ui.py` and consumes only local, redacted APIs. The unified Studio provides persistent conversations, repository browsing, before/after/Diff review, audited action traces, encrypted credential settings and three verification levels. `/` redirects to `/studio`; the retired dashboard UI is not shipped. Historical repair runs remain available through the CLI and `/runs` inspection API.
