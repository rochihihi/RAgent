"""Live Flash smoke evaluation in isolated workspaces; never edits user projects."""
import asyncio
import json
import tempfile
from pathlib import Path

from veripatch.config import Settings
from veripatch.studio_agent import StudioAgent
from veripatch.studio_domain import StudioSession
from veripatch.studio_model import StudioProviderModel
from veripatch.studio_store import StudioStore


async def main():
    model = StudioProviderModel("deepseek", Settings(
        deepseek_model="deepseek-v4-flash", reasoning_effort="low",
    ))
    cases = [
        ("missing_reference", "1", True),
        ("missing_objective", "修改 hello.py，不要运行任何命令。", True),
        ("read_only", "只读取并说明 hello.py 的作用，不修改文件、不运行命令。", False),
        ("specific_edit", "把 hello.py 中 hello() 返回的字符串改成 goodbye，不运行命令。", False),
    ]
    failures = 0
    for name, message, should_wait in cases:
        with tempfile.TemporaryDirectory(prefix="ragent-flash-eval-") as directory:
            root = Path(directory)
            target = root / "hello.py"
            target.write_text("def hello():\n    return 'hello'\n", encoding="utf-8")
            session = StudioSession(
                session_id=name, repo_root=directory, provider="deepseek",
                model="deepseek-v4-flash", reasoning_effort="low",
                approved_write_paths=[directory],
            )
            result = await StudioAgent(model, StudioStore(root / "state.db")).handle(
                session, message,
            )
            passed = (
                (result.activity == "waiting_user") == should_wait
                and (
                    "goodbye" in target.read_text(encoding="utf-8")
                    if name == "specific_edit" else
                    target.read_text(encoding="utf-8") == "def hello():\n    return 'hello'\n"
                )
                and not any(o.kind in ({"command", "test"} if name == "specific_edit"
                                       else {"command", "test", "edit", "patch"})
                            for o in result.observations)
                and result.status not in {"failed", "paused", "running"}
                and (name != "read_only" or any(o.kind == "read" for o in result.observations))
            )
            failures += not passed
            print(json.dumps({"case": name, "passed": passed,
                              "answer": result.messages[-1].content}, ensure_ascii=False),
                  flush=True)
    with tempfile.TemporaryDirectory(prefix="ragent-flash-followup-") as directory:
        root = Path(directory)
        target = root / "hello.py"
        target.write_text("VERSION = '2.4'\n", encoding="utf-8")
        session = StudioSession(
            session_id="comment-followup", repo_root=directory, provider="deepseek",
            model="deepseek-v4-flash", reasoning_effort="low",
            approved_write_paths=[directory],
        )
        agent = StudioAgent(model, StudioStore(root / "state.db"))
        await agent.handle(session, "修改 hello.py，不要运行任何命令。")
        await agent.handle(session,
            "在文件最开头加一行注释：# flash-test。不修改其他文件，仍然不要运行命令。")
        after_edit = target.read_text(encoding="utf-8")
        await agent.handle(session, "刚才具体改了什么？测试运行了吗？")
        passed = (after_edit.startswith("# flash-test\n")
                  and target.read_text(encoding="utf-8") == after_edit
                  and not any(o.kind in {"command", "test"} for o in session.observations))
        failures += not passed
        print(json.dumps({"case": "comment-followup", "passed": passed,
                          "answer": session.messages[-1].content}, ensure_ascii=False), flush=True)
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    asyncio.run(main())
