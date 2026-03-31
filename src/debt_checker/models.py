"""技術的負債の検出結果を表すデータモデル"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class IssueType(Enum):
    LONG_FUNCTION = "long_function"
    DEEP_NESTING = "deep_nesting"
    NO_DOCSTRING = "no_docstring"
    TODO_COMMENT = "todo"
    FIXME_COMMENT = "fixme"
    SHORT_VARIABLE = "short_variable"
    HIGH_COMPLEXITY = "high_complexity"


@dataclass
class Issue:
    issue_type: IssueType
    file_path: str
    line: int
    message: str
    detail: str = ""


@dataclass
class FileResult:
    file_path: str
    issues: list[Issue] = field(default_factory=list)

    @property
    def issue_count(self) -> int:
        return len(self.issues)


@dataclass
class AnalysisResult:
    file_results: list[FileResult] = field(default_factory=list)
    score: int = 100

    @property
    def total_issues(self) -> int:
        return sum(fr.issue_count for fr in self.file_results)

    @property
    def files_analyzed(self) -> int:
        return len(self.file_results)

    def issues_by_type(self) -> dict[IssueType, list[Issue]]:
        result: dict[IssueType, list[Issue]] = {}
        for fr in self.file_results:
            for issue in fr.issues:
                result.setdefault(issue.issue_type, []).append(issue)
        return result
