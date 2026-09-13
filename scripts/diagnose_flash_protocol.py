"""Reproduce a high-effort conversation, logging test responses only."""
import asyncio
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace

from veripatch.config import Settings
from veripatch.studio_agent import StudioAgent
from veripatch.studio_domain import StudioDecision, StudioSession
from veripatch.studio_model import StudioProviderModel
from veripatch.studio_store import StudioStore


class DiagnosticModel(StudioProviderModel):
    def _raw_compatible_chat(self, payload):
        response = super()._raw_compatible_chat(payload)
        message = response.choices[0].message
        print(json.dumps({"raw_content": getattr(message, "content", None),
                          "tool_calls": str(getattr(message, "tool_calls", None))},
                         ensure_ascii=True), flush=True)
        return response

    async def decide(self, context):
        try:
            return await super().decide(context)
        except Exception as exc:
            chain = []
            current = exc
            while current is not None:
                chain.append(f"{type(current).__name__}: {current}")
                current = current.__cause__
            print(json.dumps({"exception_chain": chain}, ensure_ascii=True), flush=True)
            raise


async def main():
    class Replay(StudioProviderModel):
        async def _request_decision(self, *args):
            return SimpleNamespace(), StudioDecision(
                action="respond", rationale="Report existing facts",
                message="Added a comment. Tests were not run.")

    replay = Replay("deepseek", Settings(), client=SimpleNamespace())
    try:
        await replay.decide({"changed_files": ["hello.py"],
                             "verification": {"verification_passed": False},
                             "task_contract": {"intent": "answer"},
                             "task_state": {"verification_policy": "skipped_by_user"}})
    except Exception as exc:
        print(json.dumps({"controlled_replay_error": str(exc),
                          "cause": str(exc.__cause__)}, ensure_ascii=True), flush=True)
    import sys
    if "--replay-only" in sys.argv:
        return
    model = DiagnosticModel("deepseek", Settings(
        deepseek_model="deepseek-v4-flash", reasoning_effort="high"))
    with tempfile.TemporaryDirectory(prefix="flash-protocol-") as directory:
        root = Path(directory)
        (root / "hello.py").write_text("VERSION = '2.4'\n", encoding="utf-8")
        session = StudioSession(session_id="diagnostic", repo_root=directory,
                                provider="deepseek", model="deepseek-v4-flash",
                                reasoning_effort="high", approved_write_paths=[directory])
        agent = StudioAgent(model, StudioStore(root / "state.db"))
        for message in ["修改 hello.py，不要运行任何命令。",
                        "在文件最开头加一行注释：# flash-test。不修改其他文件，仍然不要运行命令。",
                        "刚才具体改了什么？测试运行了吗？"]:
            await agent.handle(session, message)
            print(json.dumps({"user": message, "status": session.status,
                              "answer": session.messages[-1].content}, ensure_ascii=True), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
