import time
from pathlib import Path

import pytest

from veripatch.studio_tools import (
    SafeStudioCommandRunner,
    TerminalRegistry,
    UnsafeStudioCommand,
    command_capability,
    command_permission_details,
    describe_command,
    detect_project,
    is_detached_launch,
    validate_studio_command,
)


def test_managed_terminal_can_start_poll_write_and_stop(tmp_path: Path) -> None:
    command = [
        "python",
        "-u",
        "-c",
        "import sys; print('ready', flush=True); print(sys.stdin.readline().strip(), flush=True)",
    ]
    terminals = TerminalRegistry()
    started = terminals.start(tmp_path, command, approved_commands=[command])
    terminal_id = str(started["terminal_id"])
    terminals.write(tmp_path, terminal_id, "hello\n")
    deadline = time.monotonic() + 3
    output = ""
    state: dict[str, object] = {}
    while time.monotonic() < deadline:
        state = terminals.poll(tmp_path, terminal_id)
        output += str(state["output"])
        if not state["running"]:
            break
        time.sleep(0.05)
    assert "ready" in output
    assert "hello" in output
    stopped = terminals.stop(tmp_path, terminal_id)
    assert stopped["running"] is False


def test_describes_read_only_go_environment_probe() -> None:
    purpose, impact, risk = describe_command(["cmd", "/c", "where", "go", "&&", "go", "version"])

    assert "Go" in purpose
    assert "不会安装软件或修改文件" in impact
    assert risk == "low"


def test_describes_read_only_go_custom_location_probe() -> None:
    command = [
        "cmd",
        "/c",
        "if",
        "exist",
        r"D:\Go",
        "(dir",
        "/a",
        r"D:\Go)",
        "else",
        "(echo",
        "D_GO_NOT_FOUND)",
        "&",
        "where",
        "go",
        "&",
        "go",
        "version",
    ]

    purpose, impact, risk = describe_command(command)

    assert r"d:\go" in purpose.casefold()
    assert "不会安装 Go" in impact
    assert risk == "low"


def test_describes_powershell_select_string_as_read_only_code_search() -> None:
    command = [
        "powershell",
        "-NoProfile",
        "-Command",
        "$p='advanced_gui_calculator.go'; Select-String -Path $p -Pattern 'func|type'",
    ]

    purpose, impact, risk = describe_command(command)

    assert "搜索代码结构和关键词" in purpose
    assert "不会运行该程序" in impact
    assert "不会修改或删除文件" in impact
    assert risk == "low"


@pytest.mark.parametrize(
    ("command", "risk", "destructive", "recommendation"),
    [
        (["powershell", "-Command", "Remove-Item x -Recurse"], "high", True, "不确定请拒绝"),
        (["winget", "install", "Git.Git"], "high", False, "确认软件名称"),
        (["custom-tool", "opaque"], "unknown", False, "确认与当前任务一致"),
    ],
)
def test_every_command_permission_has_decision_support(
    command: list[str], risk: str, destructive: bool, recommendation: str
) -> None:
    details = command_permission_details(command)

    assert details["risk"] == risk
    assert details["destructive"] is destructive
    assert recommendation in str(details["recommendation"])
    assert details["scope"]
    assert details["recovery"]


def test_unknown_command_does_not_claim_to_be_safe() -> None:
    _purpose, impact, risk = describe_command(["custom-tool", "do-something"])

    assert "无法自动确认" in impact
    assert risk == "unknown"


def test_python_inline_recursive_delete_is_explained_as_destructive() -> None:
    command = [
        "python",
        "-c",
        "from pathlib import Path; import shutil; "
        "root=Path(r'C:\\Users\\demo\\project'); "
        "[(shutil.rmtree(p) if p.is_dir() else p.unlink()) for p in list(root.iterdir())]; "
        "remaining=list(root.iterdir()); assert not remaining",
    ]

    details = command_permission_details(command)

    assert details["destructive"] is True
    assert details["risk"] == "high"
    assert "永久清空" in details["purpose"]
    assert r"C:\Users\demo\project" in details["purpose"]
    assert "保留目录本身" in details["purpose"]
    assert "不保证进入回收站" in details["impact"]


def test_py_compile_permission_explains_exact_file_and_side_effect() -> None:
    details = command_permission_details(
        ["python", "-m", "py_compile", "game.py"],
        "先检查新写的游戏脚本是否存在语法错误，再尝试启动界面。",
    )

    assert details["risk"] == "low"
    assert details["destructive"] is False
    assert "game.py" in details["purpose"]
    assert "语法" in details["purpose"]
    assert "不会启动" in details["impact"]
    assert "__pycache__" in details["impact"]


def test_compound_powershell_build_and_launch_is_not_detached() -> None:
    command = [
        "powershell",
        "-NoProfile",
        "-Command",
        "$target='D:\\GoCalculator'; New-Item -Force $target; "
        "go build -o $target\\calculator.exe calculator.go; "
        "Start-Process $target\\calculator.exe",
    ]

    assert is_detached_launch(command) is False


def test_detects_polyglot_project(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")

    project = detect_project(tmp_path)

    assert project["stacks"] == ["Python", "Node.js"]
    assert project["markers"] == ["pyproject.toml", "package.json"]


@pytest.mark.parametrize(
    "command",
    [
        ["python", "-m", "pytest", "-q"],
        ["python", "scripts/check_output.py"],
        ["npm", "run", "build"],
        ["cargo", "clippy"],
        ["git", "diff", "--stat"],
    ],
)
def test_accepts_allowlisted_development_commands(command: list[str]) -> None:
    validate_studio_command(command)


@pytest.mark.parametrize(
    "command",
    [
        ["npm", "install"],
        ["powershell", "-Command", "Get-ChildItem"],
        ["git", "push"],
        ["python", "../script.py"],
        ["python", "script.txt"],
        ["npm", "run", "build", "&&", "whoami"],
        ["cargo", "test", "../outside"],
    ],
)
def test_rejects_mutating_or_escaping_commands(command: list[str]) -> None:
    with pytest.raises(UnsafeStudioCommand):
        validate_studio_command(command)


def test_safe_runner_executes_allowlisted_command_without_shell(tmp_path: Path) -> None:
    outcome = SafeStudioCommandRunner(tmp_path).run(["git", "status", "--short"])

    assert outcome.command == ["git", "status", "--short"]
    assert outcome.exit_code != 124


def test_safe_runner_rejects_a_missing_workspace_script_before_launch(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="missing.py"):
        SafeStudioCommandRunner(tmp_path).run(["python", "missing.py"])


def test_exact_user_approved_command_can_run_without_broad_allowlist(tmp_path: Path) -> None:
    command = ["python", "-c", "value = 1; print('approved', value)"]

    outcome = SafeStudioCommandRunner(tmp_path, approved_commands=[command]).run(command)

    assert outcome.exit_code == 0
    assert "approved" in outcome.stdout


def test_equivalent_gui_launches_share_only_the_same_target_capability(tmp_path: Path) -> None:
    cmd_launch = ["cmd", "/c", "start", "", "python", "calculator.py"]
    powershell_launch = [
        "powershell",
        "-Command",
        "Start-Process pythonw -ArgumentList calculator.py",
    ]

    capability = command_capability(cmd_launch, tmp_path)

    assert capability == "launch:calculator.py"
    assert command_capability(powershell_launch, tmp_path) == capability
    assert (
        command_capability(["cmd", "/c", "start", "", "python", "other.py"], tmp_path) != capability
    )
    assert command_capability(["python", "calculator.py"], tmp_path) is None


def test_gui_launch_accepts_an_equivalent_previously_approved_capability(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    command = ["powershell", "-Command", "Start-Process pythonw calculator.py"]
    capability = "launch:calculator.py"

    class Started:
        pid = 1234

        @staticmethod
        def poll():
            return None

    monkeypatch.setattr(
        "veripatch.studio_tools.subprocess.Popen", lambda *args, **kwargs: Started()
    )
    snapshots = iter(({100}, {100, 200}))
    monkeypatch.setattr(
        "veripatch.studio_tools._visible_window_handles", lambda: next(snapshots, {100, 200})
    )
    outcome = SafeStudioCommandRunner(tmp_path, approved_capabilities=[capability]).launch(command)

    assert outcome.exit_code == 0
    assert "1234" in outcome.stdout
    assert "window_confirmed=true" in outcome.stdout
