"""Read project metadata to propose verification commands without executing them."""

import json
from pathlib import Path


def discover_verification(root: Path, changed: list[str], override: list[str]) -> list[dict]:
    if override:
        return [{"command": override, "source": "manual", "kind": "verification"}]
    candidates = []

    def exists(name):
        path = root / name
        return path.is_file() and path.resolve().is_relative_to(root.resolve())

    def add(command, source, kind="test"):
        candidates.append({"command": command, "source": source, "kind": kind})

    suffixes = {Path(p).suffix.lower() for p in changed}
    if exists("package.json") and (
        not changed or suffixes & {".js", ".jsx", ".ts", ".tsx", ".json", ".css", ".html"}
    ):
        try:
            path = root / "package.json"
            package = (
                json.loads(path.read_text(encoding="utf-8"))
                if path.stat().st_size < 512_000
                else {}
            )
            scripts = package.get("scripts", {}) if isinstance(package, dict) else {}
            if isinstance(scripts, dict):
                manager = (
                    "pnpm" if exists("pnpm-lock.yaml") else "yarn" if exists("yarn.lock") else "npm"
                )
                for name in ("test", "typecheck", "lint", "build"):
                    body = scripts.get(name)
                    if isinstance(body, str) and body.strip() and "no test specified" not in body:
                        add([manager, "run", name], f"package.json:scripts.{name}", name)
        except (OSError, ValueError):
            pass
    if exists("Cargo.toml") and (not changed or suffixes & {".rs", ".toml"}):
        add(["cargo", "test"], "Cargo.toml")
    if exists("go.mod") and (not changed or suffixes & {".go", ".mod"}):
        add(["go", "test", "./..."], "go.mod")
    if not changed or ".py" in suffixes:
        if exists("pytest.ini"):
            add(["python", "-m", "pytest", "-q"], "pytest.ini")
        elif exists("pyproject.toml"):
            import tomllib

            try:
                path = root / "pyproject.toml"
                config = (
                    tomllib.loads(path.read_text(encoding="utf-8"))
                    if path.stat().st_size < 512_000
                    else {}
                )
                if "pytest" in config.get("tool", {}):
                    add(["python", "-m", "pytest", "-q"], "pyproject.toml:tool.pytest")
            except (OSError, ValueError, TypeError):
                pass
        files = [p for p in changed if Path(p).suffix.lower() == ".py"]
        if files:
            add(["python", "-m", "py_compile", *files], "changed Python files", "syntax")
    return candidates
