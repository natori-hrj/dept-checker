"""debt-checker CLI エントリポイント"""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .analyzers import analyze_file
from .models import AnalysisResult, IssueType
from .reporter import ISSUE_TYPE_LABELS, write_report
from .scorer import calculate_score

console = Console()

IGNORE_CHOICES = [
    "long_function",
    "deep_nesting",
    "no_docstring",
    "todo",
    "fixme",
    "short_variable",
    "complexity",
]


def _collect_python_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target] if target.suffix == ".py" else []
    return sorted(target.rglob("*.py"))


def _score_color(score: int) -> str:
    if score >= 80:
        return "green"
    if score >= 60:
        return "yellow"
    return "red"


def _display_results(result: AnalysisResult, target: str) -> None:
    """richを使って結果をターミナルに表示する"""
    # スコア表示
    color = _score_color(result.score)
    score_text = Text(f" {result.score} / 100 ", style=f"bold {color}")
    console.print()
    console.print(
        Panel(
            score_text,
            title="技術的負債スコア",
            subtitle=f"{result.files_analyzed}ファイル解析 | {result.total_issues}件検出",
            border_style=color,
        )
    )
    console.print()

    if result.total_issues == 0:
        console.print("[bold green]問題は検出されませんでした[/bold green]")
        return

    # カテゴリ別サマリ
    table = Table(title="カテゴリ別サマリ")
    table.add_column("カテゴリ", style="cyan")
    table.add_column("件数", justify="right", style="magenta")

    by_type = result.issues_by_type()
    for issue_type in IssueType:
        count = len(by_type.get(issue_type, []))
        if count > 0:
            table.add_row(ISSUE_TYPE_LABELS[issue_type], str(count))

    console.print(table)
    console.print()

    # ファイル別詳細
    for fr in sorted(result.file_results, key=lambda f: -f.issue_count):
        if fr.issue_count == 0:
            continue
        console.print(f"[bold]{fr.file_path}[/bold] ({fr.issue_count}件)")
        for issue in fr.issues:
            label = ISSUE_TYPE_LABELS[issue.issue_type]
            detail = f" [dim]({issue.detail})[/dim]" if issue.detail else ""
            console.print(f"  [yellow]L{issue.line}[/yellow] [{label}] {issue.message}{detail}")
        console.print()


@click.command()
@click.argument("target", type=click.Path(exists=True))
@click.option("--report", type=click.Path(), default=None, help="Markdownレポートの出力先")
@click.option(
    "--ignore",
    multiple=True,
    type=click.Choice(IGNORE_CHOICES, case_sensitive=False),
    help="無効化するチェック",
)
@click.option("--max-lines", default=50, show_default=True, help="関数の最大行数")
@click.option("--max-nesting", default=4, show_default=True, help="最大ネスト深度")
def main(
    target: str,
    report: str | None,
    ignore: tuple[str, ...],
    max_lines: int,
    max_nesting: int,
) -> None:
    """Python技術的負債検出ツール

    TARGET: 解析対象のファイルまたはディレクトリ
    """
    target_path = Path(target)
    ignore_set = set(ignore)

    files = _collect_python_files(target_path)
    if not files:
        console.print("[red]Pythonファイルが見つかりませんでした[/red]")
        raise SystemExit(1)

    result = AnalysisResult()
    with console.status("[bold blue]解析中...[/bold blue]"):
        for file_path in files:
            try:
                file_result = analyze_file(
                    file_path,
                    max_function_lines=max_lines,
                    max_nesting=max_nesting,
                    ignore=ignore_set,
                )
                result.file_results.append(file_result)
            except Exception as e:
                console.print(f"[red]エラー: {file_path}: {e}[/red]")

    result.score = calculate_score(result)
    _display_results(result, target)

    if report:
        report_path = Path(report)
        write_report(result, target, report_path)
        console.print(f"[green]レポートを出力しました: {report_path}[/green]")
