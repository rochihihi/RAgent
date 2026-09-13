# Threat Model

## Protected Assets

- Host files outside the selected repository.
- API keys, tokens and environment credentials.
- Test integrity and existing repository metadata.
- Host network, CPU, memory and process availability.
- Run history, patches and verification evidence.

## Untrusted Inputs

- Issue text and model output.
- Repository source, tests, configuration and pytest plugins.
- File paths, exact edits and test targets supplied through the API or CLI.

## Implemented Controls

| Risk | Control |
|---|---|
| Path traversal or symlink escape | Resolve every path and require it to remain below the repository root. |
| Model tampers with tests | Test directories and common test filenames are read-only to edit actions. |
| Partial multi-file patch or crash | Persist before/after hashes before writing, reconcile all crash windows on resume, and reject unknown drift. |
| Arbitrary command execution | Only `pytest` or `python -m pytest` argument arrays are accepted; `shell=False`. |
| Secret disclosure to tests | Remove environment keys containing token, secret, password, API key or credential markers. |
| Repository test reaches network | Docker runner uses `--network none`. |
| Resource exhaustion | Docker runner sets timeout, CPU, memory and PID limits plus a bounded tmpfs. |
| Container privilege escalation | Read-only root, dropped capabilities and `no-new-privileges`. |
| Infinite or expensive Agent loop | Maximum steps, model calls, input/output Tokens and three-identical-action termination. |
| Test mutates source repository | Docker bind mount is read-only; pytest caches and temp files are redirected to bounded tmpfs. |
| API/event leaks provider secrets | Public state drops internal snapshots and request IDs; recursive event filtering redacts credential-shaped text. |
| GUI credential capture or persistence | The page never writes keys to Web Storage and clears inputs after saving; the API accepts `SecretStr`, uses Credential Manager or a current-user DPAPI-encrypted fallback, verifies read-back, strips raw values from validation errors, never echoes values, and refuses to delete environment-managed keys. |
| Folder picker abuse or concurrency | The localhost-only endpoint requires a custom UI header (forcing cross-origin browser preflight), opens an OS-controlled directory dialog, permits only one dialog at a time and returns only the path explicitly selected by the local user. |
| Quota monitor leaks credentials | Authorization headers exist only in the outbound request; snapshots contain balances/status only and are never checkpointed. |
| False success claim | Only a non-empty diff plus deterministic passing test can succeed. |
| Misleading benchmark | Scripted tasks are labeled runtime validation, not model quality. |

## Residual Risks

- The local runner executes repository tests on the host and must be used only with trusted fixtures.
- A custom Docker image may contain vulnerable dependencies; images should be pinned and scanned in production.
- A hostile test can still consume its allowed CPU/memory budget or exploit a vulnerability in the Docker engine/kernel; a production worker should additionally use disposable VMs and pinned images.
- The local API has no authentication and therefore binds to `127.0.0.1` by default.
- The in-process background scheduler does not provide distributed locking or multi-worker failover.

## Security Regression Tests

The test suite covers path traversal, test tampering, secret stripping, dangerous pytest arguments, four transaction recovery states, workspace drift, Docker security flags, provider errors, credential write/delete boundaries, budgets, repeated actions and deterministic success gates.
