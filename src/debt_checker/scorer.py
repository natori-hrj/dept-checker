"""検出結果からスコアを算出する"""

from __future__ import annotations

from .models import AnalysisResult, IssueType

# 各IssueTypeごとの減点ウェイト
PENALTY_WEIGHTS: dict[IssueType, float] = {
    IssueType.LONG_FUNCTION: 5.0,
    IssueType.DEEP_NESTING: 5.0,
    IssueType.NO_DOCSTRING: 2.0,
    IssueType.TODO_COMMENT: 1.0,
    IssueType.FIXME_COMMENT: 1.5,
    IssueType.SHORT_VARIABLE: 1.0,
    IssueType.HIGH_COMPLEXITY: 6.0,
}


def calculate_score(result: AnalysisResult) -> int:
    """100点満点のスコアを計算する。問題が多いほど減点される。"""
    if result.files_analyzed == 0:
        return 100

    total_penalty = 0.0
    for issue_type, issues in result.issues_by_type().items():
        weight = PENALTY_WEIGHTS.get(issue_type, 1.0)
        total_penalty += len(issues) * weight

    # ファイル数で正規化し、100点から減点
    normalized_penalty = total_penalty / result.files_analyzed * 10
    score = max(0, int(100 - normalized_penalty))
    return score
