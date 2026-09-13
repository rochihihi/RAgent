import json

from veripatch.verification_discovery import discover_verification


def test_manual_command_wins(tmp_path):
    assert discover_verification(tmp_path, [], ["custom", "test"])[0]["source"] == "manual"


def test_python_config_and_syntax_are_distinct(tmp_path):
    (tmp_path / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    candidates = discover_verification(tmp_path, ["hello.py"], [])
    assert candidates[0]["command"] == ["python", "-m", "pytest", "-q"]
    assert candidates[1]["kind"] == "syntax"


def test_javascript_lockfile_and_placeholder(tmp_path):
    (tmp_path / "package.json").write_text(
        json.dumps(
            {"scripts": {"test": "echo no test specified && exit 1", "build": "vite build"}}
        ),
        encoding="utf-8",
    )
    (tmp_path / "pnpm-lock.yaml").write_text("", encoding="utf-8")
    result = discover_verification(tmp_path, ["index.js"], [])
    assert result[0]["command"] == ["pnpm", "run", "build"]


def test_malformed_metadata_and_empty_project(tmp_path):
    (tmp_path / "package.json").write_text("broken", encoding="utf-8")
    assert discover_verification(tmp_path, [], []) == []


def test_rust_and_go_candidates(tmp_path):
    (tmp_path / "Cargo.toml").write_text("", encoding="utf-8")
    (tmp_path / "go.mod").write_text("module example", encoding="utf-8")
    assert discover_verification(tmp_path, ["main.rs"], [])[0]["command"] == ["cargo", "test"]
    assert discover_verification(tmp_path, ["main.go"], [])[0]["command"] == ["go", "test", "./..."]
