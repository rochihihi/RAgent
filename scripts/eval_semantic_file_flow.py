"""Live semantic/file-flow smoke test in an isolated temporary project."""

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
    model = StudioProviderModel(
        "deepseek",
        Settings(
            deepseek_model="deepseek-v4-flash",
            reasoning_effort="high",
        ),
    )
    with tempfile.TemporaryDirectory(prefix="ragent-semantic-flow-") as directory:
        root = Path(directory)
        (root / "a.txt").write_text("hello", encoding="utf-8")
        session = StudioSession(
            session_id="semantic-flow",
            repo_root=directory,
            provider="deepseek",
            model="deepseek-v4-flash",
            reasoning_effort="high",
        )
        agent = StudioAgent(model, StudioStore(root / "state.sqlite3"), max_steps=8)
        for message in [
            "把 a.txt 重命名为 b.txt。",
            "把它复制一份，叫 c.txt。不要运行命令。",
            "刚才改了哪些文件？只回答，不修改文件、不运行命令。",
        ]:
            await asyncio.wait_for(agent.handle(session, message), timeout=180)
            print(
                json.dumps(
                    {
                        "message": message,
                        "status": session.status,
                        "intent": session.task_contract.intent,
                        "allowed": session.task_contract.allowed_actions,
                        "answer": session.messages[-1].content,
                        "files": sorted(p.name for p in root.glob("*.txt")),
                        "tools": [o.kind for o in session.observations],
                        "classification": [
                            e
                            for e in agent.store.events(session.session_id)
                            if e["event_type"] == "intent_classifier_fallback"
                        ],
                    },
                    ensure_ascii=True,
                ),
                flush=True,
            )
        assert not (root / "a.txt").exists()
        assert (root / "b.txt").read_text() == (root / "c.txt").read_text() == "hello"
        assert not any(o.kind in {"test", "command"} for o in session.observations)
        assert session.status not in {"failed", "paused", "running"}


if __name__ == "__main__":
    asyncio.run(main())
