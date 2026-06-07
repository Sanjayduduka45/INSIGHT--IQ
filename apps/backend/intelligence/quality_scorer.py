"""
InsightIQ — Data Quality Scorer

Computes a comprehensive data quality score across five dimensions:
Completeness, Uniqueness, Consistency, Validity, and Timeliness.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from intelligence.schema_detector import DatasetSchema

logger = logging.getLogger(__name__)


@dataclass
class QualityIssue:
    """A data quality issue."""

    severity: str  # critical, warning, info
    category: str  # completeness, uniqueness, consistency, validity
    column: str
    description: str
    affected_rows: int
    recommendation: str


@dataclass
class QualityReport:
    """Full data quality assessment."""

    overall_score: float  # 0-100
    completeness: float
    uniqueness: float
    consistency: float
    validity: float
    timeliness: float
    grade: str  # A, B, C, D, F
    issues: List[QualityIssue] = field(default_factory=list)
    column_scores: Dict[str, float] = field(default_factory=dict)
    summary: str = ""


def score_quality(df: pd.DataFrame, schema: DatasetSchema) -> QualityReport:
    """Compute comprehensive data quality score."""
    n = len(df)
    if n == 0:
        return QualityReport(
            overall_score=0,
            completeness=0,
            uniqueness=0,
            consistency=0,
            validity=0,
            timeliness=0,
            grade="F",
            summary="Empty dataset",
        )

    issues: List[QualityIssue] = []

    # ── 1. Completeness (missing values) ─────────────────────────
    missing_rates = df.isna().mean()
    completeness = round((1 - missing_rates.mean()) * 100, 1)

    for col in df.columns:
        mr = missing_rates[col]
        if mr > 0.5:
            issues.append(
                QualityIssue(
                    severity="critical",
                    category="completeness",
                    column=col,
                    description=f"{mr * 100:.1f}% missing values",
                    affected_rows=int(df[col].isna().sum()),
                    recommendation=f"Investigate why '{col}' has >50% missing data. Consider imputation or removal.",
                )
            )
        elif mr > 0.1:
            issues.append(
                QualityIssue(
                    severity="warning",
                    category="completeness",
                    column=col,
                    description=f"{mr * 100:.1f}% missing values",
                    affected_rows=int(df[col].isna().sum()),
                    recommendation=f"Review '{col}' for systematic missing patterns.",
                )
            )

    # ── 2. Uniqueness (duplicates) ───────────────────────────────
    dup_count = int(df.duplicated().sum())
    dup_rate = dup_count / n if n > 0 else 0
    uniqueness = round((1 - dup_rate) * 100, 1)

    if dup_rate > 0.1:
        issues.append(
            QualityIssue(
                severity="critical",
                category="uniqueness",
                column="*",
                description=f"{dup_count:,} duplicate rows ({dup_rate * 100:.1f}%)",
                affected_rows=dup_count,
                recommendation="Remove duplicate rows. Investigate data pipeline for duplication source.",
            )
        )
    elif dup_rate > 0.01:
        issues.append(
            QualityIssue(
                severity="warning",
                category="uniqueness",
                column="*",
                description=f"{dup_count:,} duplicate rows ({dup_rate * 100:.1f}%)",
                affected_rows=dup_count,
                recommendation="Review and deduplicate records.",
            )
        )

    # ── 3. Consistency (type consistency per column) ──────────────
    consistency_scores = []
    for col in df.columns:
        series = df[col].dropna()
        if series.empty:
            consistency_scores.append(100.0)
            continue
        if pd.api.types.is_numeric_dtype(series):
            # Check for extreme outliers as inconsistency signal
            if series.std() > 0:
                z_scores = np.abs((series - series.mean()) / series.std())
                inconsistent = (z_scores > 5).sum()
                score = (1 - inconsistent / len(series)) * 100
            else:
                score = 100.0
        else:
            # For strings, check for mixed casing of same value
            values = series.astype(str)
            lower_unique = values.str.lower().nunique()
            actual_unique = values.nunique()
            if actual_unique > 0:
                score = (lower_unique / actual_unique) * 100
            else:
                score = 100.0
            if score < 80:
                issues.append(
                    QualityIssue(
                        severity="info",
                        category="consistency",
                        column=col,
                        description="Inconsistent casing/formatting detected",
                        affected_rows=actual_unique - lower_unique,
                        recommendation=f"Standardize values in '{col}' (e.g., title case).",
                    )
                )
        consistency_scores.append(min(score, 100.0))

    consistency = round(np.mean(consistency_scores), 1) if consistency_scores else 100.0

    # ── 4. Validity (data type correctness) ──────────────────────
    validity_scores = []
    for col in df.columns:
        series = df[col].dropna()
        if series.empty:
            validity_scores.append(100.0)
            continue
        if pd.api.types.is_numeric_dtype(series):
            # Check for negative values in typically-positive columns
            cl = col.lower()
            if any(kw in cl for kw in ["price", "cost", "age", "count", "quantity"]):
                neg = (series < 0).sum()
                if neg > 0:
                    issues.append(
                        QualityIssue(
                            severity="warning",
                            category="validity",
                            column=col,
                            description=f"{neg} negative values in typically-positive column",
                            affected_rows=int(neg),
                            recommendation=f"Review negative values in '{col}'.",
                        )
                    )
                    validity_scores.append((1 - neg / len(series)) * 100)
                    continue
        validity_scores.append(100.0)

    validity = round(np.mean(validity_scores), 1) if validity_scores else 100.0

    # ── 5. Timeliness (for date columns) ──────────────────────────
    timeliness = 100.0
    for col in schema.date_columns[:3]:
        try:
            dates = pd.to_datetime(df[col], errors="coerce").dropna()
            if not dates.empty:
                latest = dates.max()
                age_days = (pd.Timestamp.now() - latest).days
                if age_days > 365:
                    timeliness = min(timeliness, 50.0)
                    issues.append(
                        QualityIssue(
                            severity="info",
                            category="timeliness",
                            column=col,
                            description=f"Most recent data is {age_days} days old",
                            affected_rows=0,
                            recommendation="Consider refreshing the dataset.",
                        )
                    )
                elif age_days > 90:
                    timeliness = min(timeliness, 75.0)
        except Exception:
            pass

    # ── Compute overall score ────────────────────────────────────
    weights = {
        "completeness": 0.30,
        "uniqueness": 0.20,
        "consistency": 0.20,
        "validity": 0.20,
        "timeliness": 0.10,
    }
    overall = (
        completeness * weights["completeness"]
        + uniqueness * weights["uniqueness"]
        + consistency * weights["consistency"]
        + validity * weights["validity"]
        + timeliness * weights["timeliness"]
    )

    # Column-level scores
    col_scores = {}
    for col in df.columns:
        miss_score = (1 - missing_rates.get(col, 0)) * 100
        col_scores[col] = round(miss_score, 1)

    grade = _score_to_grade(overall)

    # Issues sorted by severity
    severity_order = {"critical": 0, "warning": 1, "info": 2}
    issues.sort(key=lambda i: severity_order.get(i.severity, 3))

    return QualityReport(
        overall_score=round(overall, 1),
        completeness=completeness,
        uniqueness=uniqueness,
        consistency=consistency,
        validity=validity,
        timeliness=timeliness,
        grade=grade,
        issues=issues[:20],  # Top 20 issues
        column_scores=col_scores,
        summary=_generate_summary(overall, grade, len(issues)),
    )


def _score_to_grade(score: float) -> str:
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    return "F"


def _generate_summary(score: float, grade: str, issue_count: int) -> str:
    if grade == "A":
        return (
            f"Excellent data quality (Score: {score:.0f}/100). {issue_count} minor issues detected."
        )
    elif grade == "B":
        return f"Good data quality (Score: {score:.0f}/100). {issue_count} issues need attention."
    elif grade == "C":
        return f"Fair data quality (Score: {score:.0f}/100). {issue_count} issues require review."
    elif grade == "D":
        return (
            f"Poor data quality (Score: {score:.0f}/100). {issue_count} significant issues found."
        )
    return f"Critical data quality issues (Score: {score:.0f}/100). {issue_count} issues need immediate attention."
