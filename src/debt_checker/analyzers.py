"""AST解析による技術的負債検出"""

from __future__ import annotations

import ast
import re
import tokenize
from io import StringIO
from pathlib import Path

from .models import FileResult, Issue, IssueType

TODO_PATTERN = re.compile(r"#\s*TODO\b", re.IGNORECASE)
FIXME_PATTERN = re.compile(r"#\s*FIXME\b", re.IGNORECASE)


def analyze_file(
    file_path: Path,
    *,
    max_function_lines: int = 50,
    max_nesting: int = 4,
    ignore: set[str] | None = None,
) -> FileResult:
    """単一ファイルを解析して技術的負債を検出する"""
    ignore = ignore or set()
    source = file_path.read_text(encoding="utf-8")
    result = FileResult(file_path=str(file_path))

    try:
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError:
        return result

    lines = source.splitlines()
    str_path = str(file_path)

    if "long_function" not in ignore:
        result.issues.extend(_check_long_functions(tree, str_path, max_function_lines))

    if "deep_nesting" not in ignore:
        result.issues.extend(_check_deep_nesting(tree, str_path, max_nesting))

    if "no_docstring" not in ignore:
        result.issues.extend(_check_no_docstring(tree, str_path))

    if "todo" not in ignore:
        result.issues.extend(_check_todo_comments(lines, str_path))

    if "fixme" not in ignore:
        result.issues.extend(_check_fixme_comments(lines, str_path))

    if "short_variable" not in ignore:
        result.issues.extend(_check_short_variables(tree, str_path))

    if "complexity" not in ignore:
        result.issues.extend(_check_complexity(tree, str_path))

    return result


def _get_function_end_line(node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    """関数の最終行を取得する"""
    return node.end_lineno or node.lineno


def _check_long_functions(
    tree: ast.Module, file_path: str, max_lines: int
) -> list[Issue]:
    issues: list[Issue] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            end = _get_function_end_line(node)
            length = end - node.lineno + 1
            if length > max_lines:
                issues.append(
                    Issue(
                        issue_type=IssueType.LONG_FUNCTION,
                        file_path=file_path,
                        line=node.lineno,
                        message=f"関数 '{node.name}' が長すぎます ({length}行)",
                        detail=f"最大{max_lines}行を推奨",
                    )
                )
    return issues


def _get_nesting_depth(node: ast.AST) -> int:
    """ノードのネスト深度を再帰的に計算する"""
    nesting_nodes = (
        ast.If, ast.For, ast.While, ast.With,
        ast.Try, ast.ExceptHandler,
        ast.AsyncFor, ast.AsyncWith,
    )
    max_depth = 0
    for child in ast.iter_child_nodes(node):
        child_depth = _get_nesting_depth(child)
        if isinstance(child, nesting_nodes):
            child_depth += 1
        max_depth = max(max_depth, child_depth)
    return max_depth


def _check_deep_nesting(
    tree: ast.Module, file_path: str, max_nesting: int
) -> list[Issue]:
    issues: list[Issue] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            depth = _get_nesting_depth(node)
            if depth > max_nesting:
                issues.append(
                    Issue(
                        issue_type=IssueType.DEEP_NESTING,
                        file_path=file_path,
                        line=node.lineno,
                        message=f"関数 '{node.name}' のネストが深すぎます (深度{depth})",
                        detail=f"最大{max_nesting}を推奨",
                    )
                )
    return issues


def _check_no_docstring(tree: ast.Module, file_path: str) -> list[Issue]:
    issues: list[Issue] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not ast.get_docstring(node):
                issues.append(
                    Issue(
                        issue_type=IssueType.NO_DOCSTRING,
                        file_path=file_path,
                        line=node.lineno,
                        message=f"関数 '{node.name}' にdocstringがありません",
                    )
                )
    return issues


def _check_todo_comments(lines: list[str], file_path: str) -> list[Issue]:
    issues: list[Issue] = []
    for i, line in enumerate(lines, 1):
        if TODO_PATTERN.search(line):
            issues.append(
                Issue(
                    issue_type=IssueType.TODO_COMMENT,
                    file_path=file_path,
                    line=i,
                    message=f"TODOコメント: {line.strip()}",
                )
            )
    return issues


def _check_fixme_comments(lines: list[str], file_path: str) -> list[Issue]:
    issues: list[Issue] = []
    for i, line in enumerate(lines, 1):
        if FIXME_PATTERN.search(line):
            issues.append(
                Issue(
                    issue_type=IssueType.FIXME_COMMENT,
                    file_path=file_path,
                    line=i,
                    message=f"FIXMEコメント: {line.strip()}",
                )
            )
    return issues


def _check_short_variables(tree: ast.Module, file_path: str) -> list[Issue]:
    """1文字の変数名を検出する（ループ変数 i, j, k, _ は除外）"""
    issues: list[Issue] = []
    allowed = {"_", "i", "j", "k", "x", "y", "z"}

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and len(target.id) == 1:
                    if target.id not in allowed:
                        issues.append(
                            Issue(
                                issue_type=IssueType.SHORT_VARIABLE,
                                file_path=file_path,
                                line=target.lineno,
                                message=f"短すぎる変数名 '{target.id}'",
                                detail="意味のある名前を推奨",
                            )
                        )
    return issues


def _calculate_complexity(node: ast.AST) -> int:
    """循環的複雑度を計算する（McCabe方式）"""
    complexity = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.IfExp)):
            complexity += 1
        elif isinstance(child, (ast.For, ast.AsyncFor, ast.While)):
            complexity += 1
        elif isinstance(child, ast.ExceptHandler):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += len(child.values) - 1
        elif isinstance(child, ast.Assert):
            complexity += 1
    return complexity


def _check_complexity(
    tree: ast.Module, file_path: str, threshold: int = 10
) -> list[Issue]:
    issues: list[Issue] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            complexity = _calculate_complexity(node)
            if complexity > threshold:
                issues.append(
                    Issue(
                        issue_type=IssueType.HIGH_COMPLEXITY,
                        file_path=file_path,
                        line=node.lineno,
                        message=f"関数 '{node.name}' の複雑度が高すぎます (CC={complexity})",
                        detail=f"閾値{threshold}以下を推奨",
                    )
                )
    return issues
