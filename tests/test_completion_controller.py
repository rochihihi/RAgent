import asyncio

from veripatch.studio_agent import StudioAgent
from veripatch.studio_domain import StudioDecision, StudioSession
from veripatch.studio_store import StudioStore
from veripatch.workspace import SafeWorkspace


def setup(tmp_path):
    s = StudioSession(
        session_id="completion",
        repo_root=str(tmp_path),
        provider="openai",
        model="test",
        reasoning_effort="low",
        permission_mode="full",
        status="running",
    )
    return StudioAgent(None, StudioStore(tmp_path / "state.sqlite3")), s, SafeWorkspace(tmp_path)


def test_text_edit_move_copy_complete_without_commands(tmp_path):
    agent, session, workspace = setup(tmp_path)
    for d in [
        StudioDecision(action="create", path="a.txt", content="hello", rationale="create"),
        StudioDecision(
            action="edit", path="a.txt", old_text="hello", new_text="world", rationale="edit"
        ),
        StudioDecision(action="move_file", path="a.txt", destination="b.txt", rationale="move"),
        StudioDecision(action="copy_file", path="b.txt", destination="c.txt", rationale="copy"),
    ]:
        before = session.action_epoch
        agent._execute(session, workspace, d)
        assert session.action_epoch == before + 1
    assert agent._has_file_operation_evidence(session)
    assert agent._execute(
        session,
        workspace,
        StudioDecision(action="finish", rationale="done", message="已完成文件操作。"),
    )
    assert session.status == "completed"
    assert not session.verification_passed


def test_completion_rejection_stops_without_new_evidence(tmp_path):
    agent, session, workspace = setup(tmp_path)
    agent._execute(
        session,
        workspace,
        StudioDecision(action="create", path="a.py", content="x=1", rationale="create"),
    )
    finish = StudioDecision(action="finish", rationale="done", message="已完成。")
    assert not agent._execute(session, workspace, finish)
    assert agent._execute(session, workspace, finish)
    assert session.status == "paused"
    assert "完成条件未发生变化" in session.messages[-1].content


def test_batch_commits_only_successful_epochs(tmp_path):
    agent, session, workspace = setup(tmp_path)
    agent._execute_batch(
        session,
        workspace,
        [
            StudioDecision(action="create", path="a.txt", content="ok", rationale="create"),
            StudioDecision(
                action="create", path="a.txt", content="overwrite", rationale="conflict"
            ),
            StudioDecision(action="create", path="b.txt", content="bad", rationale="must not run"),
        ],
        "创建文件",
    )
    assert session.action_epoch == 1
    assert not (tmp_path / "b.txt").exists()
    assert session.observations[-1].kind == "tool_error"


def test_verified_fallback_never_leaves_running(tmp_path):
    agent, session, workspace = setup(tmp_path)
    agent._finish_from_verified_evidence(session, workspace, "fallback")
    assert session.status != "running"


def test_public_loop_never_returns_orphan_running_state(tmp_path):
    agent, session, _ = setup(tmp_path)

    async def orphan(*args, **kwargs):
        return session

    agent._handle = orphan
    asyncio.run(agent.handle(session, "继续"))
    assert session.status == "paused"


def test_external_edits_invalidate_file_verification(tmp_path):
    agent, session, workspace = setup(tmp_path)
    agent._execute(
        session,
        workspace,
        StudioDecision(action="create", path="a.txt", content="ok", rationale="create"),
    )
    (tmp_path / "a.txt").write_text("user edit", encoding="utf-8")
    assert not agent._has_file_operation_evidence(session)


def test_batch_permission_resume_retains_remaining_actions(tmp_path):
    from veripatch.studio_domain import PermissionMode, StudioReply
    from veripatch.studio_permissions import fingerprint

    actions = [
        StudioDecision(action="create", path=name, content="ok", rationale="create")
        for name in ["a.txt", "b.txt"]
    ]

    class Model:
        async def decide(self, context):
            return StudioReply(
                decision=StudioDecision(
                    action="finish", rationale="done", message="已创建 a.txt 和 b.txt。"
                )
            )

    agent, session, workspace = setup(tmp_path)
    agent.model = Model()
    session.permission_mode = PermissionMode.ASK
    assert agent._execute_batch(session, workspace, actions, "创建 a.txt 和 b.txt")
    assert session.remaining_actions == actions[1:]
    for d in actions:
        session.once_grants.append(fingerprint(d))
        session.resume_decision = d
        session.pending_permission = None
        asyncio.run(
            agent.handle(
                session,
                "创建 a.txt 和 b.txt",
                continuation=True,
                record_user_message=False,
                resume_after_permission=True,
            )
        )
    assert session.status == "completed"
    assert session.action_epoch == 2
    assert not session.remaining_actions


def test_same_test_output_is_not_progress(tmp_path):
    from veripatch.studio_completion import CompletionCheck
    from veripatch.studio_domain import StudioObservation

    agent, session, _ = setup(tmp_path)
    check = CompletionCheck("needs_verification", ("test failed",))
    for duration in [1, 2]:
        session.observations.append(
            StudioObservation(
                kind="test",
                summary="failed",
                payload={
                    "command": ["pytest"],
                    "exit_code": 1,
                    "stderr": "failure",
                    "duration_seconds": duration,
                },
            )
        )
        terminal = agent._reject_completion(session, check)
    assert terminal and session.status == "paused"


def test_model_handoff_uses_controller_completion():
    from veripatch.studio_model import StudioProviderModel

    reply = StudioDecision(action="respond", rationale="done", message="已重命名文件。")
    assert not StudioProviderModel._is_unverified_execution_handoff(
        reply,
        {
            "changed_files": ["a.txt", "b.txt"],
            "task_contract": {"intent": "change"},
            "completion": {"requires_commands": False},
        },
    )


def test_document_patch_uses_same_content_verification(tmp_path):
    agent, session, workspace = setup(tmp_path)
    (tmp_path / "a.md").write_text("old\n", encoding="utf-8")
    agent._execute(
        session,
        workspace,
        StudioDecision(
            action="apply_patch",
            rationale="更新文档",
            patch="--- a/a.md\n+++ b/a.md\n@@ -1 +1 @@\n-old\n+new\n",
        ),
    )
    assert agent._has_file_operation_evidence(session)
    assert not agent._requires_command_verification(session)
