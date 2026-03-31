"""Markdownレポート生成"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .models import AnalysisResult, IssueType

ISSUE_TYPE_LABELS: dict[IssueType, str] = {
    IssueType.LONG_FUNCTION: "長すぎる関数",
    IssueType.DEEP_NESTING: "深すぎるネスト",
    IssueType.NO_DOCSTRING: "docstringなし",
    IssueType.TODO_COMMENT: "TODOコメント",
    IssueType.FIXME_COMMENT: "FIXMEコメント",
    IssueType.SHORT_VARIABLE: "短すぎる変数名",
    IssueType.HIGH_COMPLEXITY: "高い循環的複雑度",
}


def generate_markdown(result: AnalysisResult, target: str) -> str:
    """AnalysisResultからMarkdownレポートを生成する"""
    lines: list[str] = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines.append("# 技術的負債レポート")
    lines.append("")
    lines.append(f"- **対象**: `{target}`")
    lines.append(f"- **生成日時**: {now}")
    lines.append(f"- **解析ファイル数**: {result.files_analyzed}")
    lines.append(f"- **検出件数**: {result.total_issues}")
    lines.append(f"- **スコア**: {result.score} / 100")
    lines.append("")

    # カテゴリ別サマリ
    lines.append("## カテゴリ別サマリ")
    lines.append("")
    lines.append("| カテゴリ | 件数 |")
    lines.append("|----------|------|")
    by_type = result.issues_by_type()
    for issue_type in IssueType:
        count = len(by_type.get(issue_type, []))
        if count > 0:
            label = ISSUE_TYPE_LABELS[issue_type]
            lines.append(f"| {label} | {count} |")
    lines.append("")

    # ファイル別詳細
    lines.append("## ファイル別詳細")
    lines.append("")
    for fr in sorted(result.file_results, key=lambda f: -f.issue_count):
        if fr.issue_count == 0:
            continue
        lines.append(f"### `{fr.file_path}` ({fr.issue_count}件)")
        lines.append("")
        for issue in fr.issues:
            label = ISSUE_TYPE_LABELS[issue.issue_type]
            detail = f" ({issue.detail})" if issue.detail else ""
            lines.append(f"- **L{issue.line}** [{label}] {issue.message}{detail}")
        lines.append("")

    return "\n".join(lines)


def write_report(result: AnalysisResult, target: str, output_path: Path) -> None:
    """Markdownレポートをファイルに書き出す"""
    content = generate_markdown(result, target)
    output_path.write_text(content, encoding="utf-8")
