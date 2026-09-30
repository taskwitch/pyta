"""
This file contains functions for automatically fixing style issues (e.g. pycodestyle warnings)
using autopep8 followed by Black.
"""

import ast
import difflib
import subprocess
import sys
from typing import Optional

import autopep8

# Codes that autopep8 ignores by default; kept so that passing a custom ignore list
# does not start fixing things autopep8 would normally leave alone.
_AUTOPEP8_DEFAULT_IGNORE = ["E226", "E24", "W50", "W690"]


def fix_source(
    source: str,
    autoformat_options: list[str],
    max_linelen: Optional[int],
    pycodestyle_ignore: Optional[list[str]] = None,
) -> str:
    """Return *source* with fixable style issues corrected.

    The fixes are applied with autopep8 (skipping any codes in *pycodestyle_ignore*),
    followed by Black. If *source* is not valid Python, it is returned unchanged.
    """
    try:
        ast.parse(source)
    except (SyntaxError, ValueError):
        return source

    options: dict = {"ignore": _AUTOPEP8_DEFAULT_IGNORE + list(pycodestyle_ignore or [])}
    if max_linelen:
        options["max_line_length"] = max_linelen
    fixed = autopep8.fix_code(source, options=options)

    black_args = [sys.executable, "-m", "black", "-q"]
    if max_linelen:
        black_args.append(f"--line-length={max_linelen}")
    black_args.extend("--" + arg for arg in autoformat_options)
    result = subprocess.run(
        black_args + ["-"], input=fixed, encoding="utf-8", capture_output=True, check=False
    )
    # If Black fails (e.g. it cannot parse the autopep8 output), keep the autopep8 result.
    return result.stdout if result.returncode == 0 else fixed


def run_autofix(
    file_path: str,
    autoformat_options: list[str],
    max_linelen: Optional[int],
    pycodestyle_ignore: Optional[list[str]] = None,
) -> None:
    """Fix style issues in the given file in place. The file is only written if it changes."""
    with open(file_path, encoding="utf-8", newline="") as f:
        source = f.read()
    fixed = fix_source(source, autoformat_options, max_linelen, pycodestyle_ignore)
    if fixed != source:
        with open(file_path, "w", encoding="utf-8", newline="") as f:
            f.write(fixed)


def diff_autofix(
    file_path: str,
    autoformat_options: list[str],
    max_linelen: Optional[int],
    pycodestyle_ignore: Optional[list[str]] = None,
) -> str:
    """Return a unified diff of the fixes that would be applied to the file, without writing it."""
    with open(file_path, encoding="utf-8", newline="") as f:
        source = f.read()
    fixed = fix_source(source, autoformat_options, max_linelen, pycodestyle_ignore)
    return "".join(
        difflib.unified_diff(
            source.splitlines(keepends=True),
            fixed.splitlines(keepends=True),
            fromfile=file_path,
            tofile=file_path + " (fixed)",
        )
    )
