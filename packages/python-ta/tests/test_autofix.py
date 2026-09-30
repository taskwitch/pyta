"""Tests for the --fix / --diff automatic style fixing."""

import io
import textwrap

from click.testing import CliRunner

import python_ta
from python_ta.util.autofix import diff_autofix, fix_source, run_autofix

BAD = textwrap.dedent(
    """\
    import os
    def f(x):
        return x
    class A:
        def g(self): pass
        def h(self): pass
    y = f(1)
    """
)
OPTIONS = ["skip-string-normalization"]


def test_fix_source_adds_blank_lines() -> None:
    fixed = fix_source(BAD, OPTIONS, 100)
    assert "import os\n\n\ndef f(x):" in fixed
    assert "\n\n\nclass A:" in fixed
    assert "\n\n\ny = f(1)" in fixed


def test_fix_source_is_idempotent() -> None:
    once = fix_source(BAD, OPTIONS, 100)
    assert fix_source(once, OPTIONS, 100) == once


def test_fix_source_leaves_syntax_errors_alone() -> None:
    source = "def f(:\n    pass\n"
    assert fix_source(source, OPTIONS, 100) == source


def test_run_autofix_writes_file(tmp_path) -> None:
    file = tmp_path / "a.py"
    file.write_text(BAD)
    run_autofix(str(file), OPTIONS, 100)
    assert file.read_text() == fix_source(BAD, OPTIONS, 100)


def test_diff_autofix_does_not_modify_file(tmp_path) -> None:
    file = tmp_path / "a.py"
    file.write_text(BAD)
    diff = diff_autofix(str(file), OPTIONS, 100)
    assert "+def f(x):" not in diff and "+\n" in diff
    assert file.read_text() == BAD


def test_check_all_fix_removes_blank_line_warnings(tmp_path) -> None:
    file = tmp_path / "a.py"
    file.write_text(BAD)
    output = io.StringIO()
    reporter = python_ta.check_all(
        str(file), config={"output-format": "pyta-json"}, output=output, fix=True
    )
    assert "E302" not in output.getvalue()
    assert "E305" not in output.getvalue()
    assert file.read_text() == fix_source(BAD, OPTIONS, 100)


def test_check_all_diff_leaves_file_untouched(tmp_path, capsys) -> None:
    file = tmp_path / "a.py"
    file.write_text(BAD)
    python_ta.check_all(
        str(file), config={"output-format": "pyta-json"}, output=io.StringIO(), diff=True
    )
    assert file.read_text() == BAD
    assert "(fixed)" in capsys.readouterr().out
