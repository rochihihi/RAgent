from pathlib import Path

from veripatch.indexing import PythonSymbolIndex


def test_symbol_index_finds_function(tmp_path: Path) -> None:
    (tmp_path / "sample.py").write_text(
        'def calculate_total(value: int) -> int:\n    """Calculate a total."""\n    return value\n',
        encoding="utf-8",
    )
    index = PythonSymbolIndex(tmp_path).build()
    matches = index.lookup("calculate total")
    assert matches
    assert matches[0].name == "calculate_total"
    assert index.summary()["symbols"] == 1


def test_symbol_index_handles_nested_async_symbols_and_parse_errors(tmp_path: Path) -> None:
    (tmp_path / "service.py").write_text(
        'class Service:\n    """API service."""\n    async def fetch(self):\n        return 1\n',
        encoding="utf-8",
    )
    (tmp_path / "broken.py").write_text("def broken(:\n", encoding="utf-8")
    ignored = tmp_path / ".venv"
    ignored.mkdir()
    (ignored / "hidden.py").write_text("def hidden(): pass\n", encoding="utf-8")
    index = PythonSymbolIndex(tmp_path).build()
    matches = index.lookup("Service fetch")
    assert [record.qualified_name for record in matches] == ["Service.fetch", "Service"]
    assert matches[1].as_dict()["docstring"] == "API service."
    assert "broken.py" in index.parse_errors
    assert index.lookup("  ") == []
    assert index.summary() == {"python_files": 1, "symbols": 2, "parse_errors": 1}
