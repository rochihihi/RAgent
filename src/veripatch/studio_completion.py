"""Controller-owned completion policy shared by all execution routes."""

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path

from veripatch.studio_domain import StudioSession, TaskVerificationPolicy, VerificationMode

MUTATIONS = {"edit", "create", "patch", "move", "copy", "delete", "git_restore"}
DOCUMENTS = {".txt", ".md", ".rst"}


def effects(session: StudioSession):
    result = {}
    for item in session.observations:
        if item.kind not in MUTATIONS:
            continue
        for path in [
            item.payload.get("path"),
            item.payload.get("source"),
            item.payload.get("destination"),
            *item.payload.get("paths", []),
        ]:
            if path in session.turn_changed_files:
                result[path] = item
    return result


def file_effects_verified(session: StudioSession) -> bool:
    latest = effects(session)
    if not session.turn_changed_files:
        return False
    for name in session.turn_changed_files:
        item = latest.get(name)
        if item is None:
            return False
        path = Path(session.repo_root) / name
        if item.kind == "delete" or (item.kind == "move" and name == item.payload.get("source")):
            if os.path.lexists(path):
                return False
            continue
        try:
            if not path.is_file():
                return False
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            return False
        expected = item.payload.get("content_hashes", {}).get(name) or item.payload.get(
            "content_sha256"
        )
        if actual != expected:
            return False
        if item.kind not in {"move", "copy"} and path.suffix.lower() not in DOCUMENTS:
            return False
    return True


def requires_commands(session: StudioSession) -> bool:
    policy = session.task_state.verification_policy if session.task_state else None
    if policy is TaskVerificationPolicy.SKIPPED_BY_USER:
        return False
    if (
        policy is TaskVerificationPolicy.REQUIRED_BY_USER
        or session.verification_mode is VerificationMode.STRICT
    ):
        return True
    return bool(session.turn_changed_files) and not file_effects_verified(session)


@dataclass(frozen=True)
class CompletionCheck:
    state: str
    reasons: tuple[str, ...] = ()


def assess(session: StudioSession, unmet: list[str]) -> CompletionCheck:
    if session.pending_permission:
        return CompletionCheck("waiting_permission")
    if unmet:
        return CompletionCheck("blocked", tuple(unmet))
    if session.verification_mode is VerificationMode.STRICT and not session.turn_changed_files:
        return CompletionCheck("needs_verification", ("严格模式尚未产生修改",))
    if (
        session.verification_mode is not VerificationMode.QUICK
        and requires_commands(session)
        and not session.verification_passed
    ):
        return CompletionCheck("needs_verification", ("尚无满足任务要求的验证证据",))
    return CompletionCheck("ready")
