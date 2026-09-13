"""Python AST symbol indexing used for structure-aware context retrieval."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

IGNORED_DIRECTORIES = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "venv",
}


@dataclass(frozen=True, slots=True)
class SymbolRecord:
    name: str
    qualified_name: str
    kind: str
    path: str
    line: int
    end_line: int
    docstring: str | None = None

    def as_dict(self) -> dict[str, str | int | None]:
        return {
            "name": self.name,
            "qualified_name": self.qualified_name,
            "kind": self.kind,
            "path": self.path,
            "line": self.line,
            "end_line": self.end_line,
            "docstring": self.docstring,
        }


class _SymbolVisitor(ast.NodeVisitor):
    def __init__(self, relative_path: str) -> None:
        self.relative_path = relative_path
        self.scope: list[str] = []
        self.records: list[SymbolRecord] = []

    def _record(self, node: ast.AST, name: str, kind: str) -> None:
        qualified = ".".join([*self.scope, name])
        docstring = (
            ast.get_docstring(node)
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
            else None
        )
        self.records.append(
            SymbolRecord(
                name=name,
                qualified_name=qualified,
                kind=kind,
                path=self.relative_path,
                line=getattr(node, "lineno", 1),
                end_line=getattr(node, "end_lineno", getattr(node, "lineno", 1)),
                docstring=docstring,
            )
        )

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._record(node, node.name, "class")
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._record(node, node.name, "function")
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._record(node, node.name, "async_function")
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()


class PythonSymbolIndex:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.records: list[SymbolRecord] = []
        self.parse_errors: dict[str, str] = {}

    def build(self) -> PythonSymbolIndex:
        self.records.clear()
        self.parse_errors.clear()
        for path in self.root.rglob("*.py"):
            if any(part in IGNORED_DIRECTORIES for part in path.relative_to(self.root).parts):
                continue
            relative = path.relative_to(self.root).as_posix()
            try:
                source = path.read_text(encoding="utf-8")
                tree = ast.parse(source, filename=relative)
            except (OSError, SyntaxError, UnicodeDecodeError) as exc:
                self.parse_errors[relative] = str(exc)
                continue
            visitor = _SymbolVisitor(relative)
            visitor.visit(tree)
            self.records.extend(visitor.records)
        return self

    def lookup(self, query: str, limit: int = 20) -> list[SymbolRecord]:
        tokens = {token.casefold() for token in query.replace(".", " ").split() if token}
        if not tokens:
            return []

        def score(record: SymbolRecord) -> tuple[int, int, str]:
            name = record.name.casefold()
            qualified = record.qualified_name.casefold()
            path = record.path.casefold()
            doc = (record.docstring or "").casefold()
            points = 0
            for token in tokens:
                if token == name:
                    points += 10
                elif token in name:
                    points += 6
                if token in qualified:
                    points += 4
                if token in path:
                    points += 2
                if token in doc:
                    points += 1
            return (-points, record.line, record.path)

        matches = [record for record in self.records if score(record)[0] < 0]
        return sorted(matches, key=score)[:limit]

    def summary(self) -> dict[str, int]:
        return {
            "python_files": len({record.path for record in self.records}),
            "symbols": len(self.records),
            "parse_errors": len(self.parse_errors),
        }
