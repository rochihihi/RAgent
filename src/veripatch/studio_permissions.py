"""Execution approvals, independent of task intent and filesystem boundaries."""

from veripatch.studio_domain import PermissionMode, StudioDecision, StudioSession
from veripatch.studio_tools import UnsafeStudioCommand, validate_studio_command

READ_ONLY = {
    "list_files",
    "search",
    "read",
    "git_status",
    "git_diff",
    "git_log",
    "poll_terminal",
    "inspect_processes",
    "respond",
    "finish",
    "fail",
    "request_permission",
    "batch",
}
IMPORTANT = {
    "delete_path",
    "git_restore",
    "git_commit",
    "git_branch",
    "write_terminal",
    "stop_terminal",
    "start_terminal",
}


def fingerprint(decision: StudioDecision) -> str:
    return decision.model_dump_json(exclude={"rationale", "message"}, exclude_none=True)


def requires_approval(session: StudioSession, decision: StudioDecision) -> bool:
    if decision.action.value == "git_branch" and not decision.branch:
        return False
    if decision.action.value in READ_ONLY:
        return False
    key = fingerprint(decision)
    if key in session.action_grants or key in session.once_grants:
        return False
    if (
        decision.action.value in {"run_command", "run_tests", "start_terminal"}
        and decision.command in session.approved_commands
    ):
        return False
    if session.permission_mode == PermissionMode.FULL:
        return False
    if session.permission_mode == PermissionMode.ASK:
        return True
    if decision.action.value in IMPORTANT:
        return True
    if decision.action.value in {"run_command", "run_tests"}:
        try:
            validate_studio_command(decision.command or session.test_command)
        except UnsafeStudioCommand:
            return True
    return False
