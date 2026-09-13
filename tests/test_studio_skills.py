import asyncio

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from veripatch import studio_skills as skills
from veripatch.config import Settings
from veripatch.studio_agent import StudioAgent
from veripatch.studio_api import create_studio_router
from veripatch.studio_domain import StudioAction, StudioDecision, StudioReply, StudioSession
from veripatch.studio_store import StudioStore

CONTENT = "---\nname: interview\ndescription: 面试陪练\n---\n一次只问一道题。"


def test_install_select_and_no_overwrite(tmp_path):
    skills.install(str(tmp_path), CONTENT)
    assert skills.discover(str(tmp_path))[0]["name"] == "interview"
    assert skills.selected(str(tmp_path), ["interview"])[0]["content"] == CONTENT
    assert skills.selected(str(tmp_path), []) == []
    with pytest.raises(FileExistsError):
        skills.install(str(tmp_path), CONTENT)
    with pytest.raises(ValueError):
        skills.selected(str(tmp_path), ["absent"])


@pytest.mark.parametrize(
    "content", ["plain", CONTENT.replace("interview", "../outside"), "x" * 12001]
)
def test_invalid_import(tmp_path, content):
    with pytest.raises(ValueError):
        skills.install(str(tmp_path), content)
    assert not (tmp_path / ".agents").exists()


def test_selected_skill_reaches_model(tmp_path):
    skills.install(str(tmp_path), CONTENT)

    class Model:
        async def decide(self, context):
            assert context["skills"]["selected"][0]["content"] == CONTENT
            assert "not authorization" in context["skills"]["rule"]
            return StudioReply(
                decision=StudioDecision(
                    action=StudioAction.RESPOND,
                    rationale="面试陪练",
                    message="请介绍 Python 的生成器。",
                )
            )

    session = StudioSession(
        session_id="skills",
        repo_root=str(tmp_path),
        provider="deepseek",
        model="test",
        reasoning_effort="low",
        enabled_skills=["interview"],
    )
    asyncio.run(
        StudioAgent(Model(), StudioStore(tmp_path / "state.db")).handle(session, "陪我面试")
    )
    assert "生成器" in session.messages[-1].content


def test_skill_api_persists_selection_and_rejects_overwrite(tmp_path):
    db = tmp_path / "state.db"
    store = StudioStore(db)
    session = StudioSession(
        session_id="api-skills",
        repo_root=str(tmp_path),
        provider="deepseek",
        model="test",
        reasoning_effort="low",
    )
    store.save(session, "created", {})
    app = FastAPI()
    app.include_router(create_studio_router(Settings(database_path=db)))
    with TestClient(app) as client:
        url = "/studio-api/sessions/api-skills/skills"
        assert client.post(url, json={"content": CONTENT}).status_code == 201
        assert client.post(url, json={"content": CONTENT}).status_code == 409
        assert client.put(url, json={"names": ["interview"]}).status_code == 200
        assert client.get(url).json()["enabled"] == ["interview"]
        assert store.load(session.session_id).enabled_skills == ["interview"]
        assert client.put(url, json={"names": ["absent"]}).status_code == 400
        running = store.load(session.session_id)
        running.status = "running"
        store.save(running, "running", {})
        assert client.put(url, json={"names": []}).status_code == 409


def test_compaction_does_not_truncate_skill(tmp_path):
    agent = StudioAgent(None, StudioStore(tmp_path / "state.db"))
    context = {
        "skills": {"selected": [{"content": "instruction" * 500}]},
        "messages": [{"content": "old" * 15000}],
    }
    fitted, _, _ = agent._fit_context(context)
    assert fitted["skills"] == context["skills"]
    assert agent._compact_retry_context(context)["skills"] == context["skills"]
