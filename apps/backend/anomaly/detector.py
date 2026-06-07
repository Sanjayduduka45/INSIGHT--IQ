"""
InsightIQ — Anomaly Detection Engine V2

Multi-method anomaly detection using:
1. Isolation Forest
2. Z-Score
3. IQR (Interquartile Range)
4. Robust MAD (Median Absolute Deviation)
5. Seasonal / Rolling Window Deviation
Combines scores using a consensus-based model to categorize severity.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


@dataclass
class DetectedAnomaly:
    index: int
    severity: str          # critical, high, medium, low
    score: float           # Anomaly score (0-1)
    method: str            # Combined methods list e.g. "Isolation Forest, Z-Score, MAD"
    columns_flagged: List[str]
    values: Dict[str, Any]
    explanation: str
    business_impact: str
    recommendation: str
    affected_kpi: str
    likely_cause: str
    expected_range: str


@dataclass
class AnomalyReport:
    total_records: int
    total_anomalies: int
    anomaly_rate: float
    severity_breakdown: Dict[str, int]
    anomalies: List[DetectedAnomaly]
    column_anomaly_counts: Dict[str, int]
    summary: str


def detect_anomalies(
    df: pd.DataFrame,
    numeric_cols: List[str],
    contamination: float = 0.05,
    methods: Optional[List[str]] = None,
) -> AnomalyReport:
    """Run multi-method consensus anomaly detection on a dataset."""
    cols = [c for c in numeric_cols if c in df.columns][:10]
    
    if not cols or len(df) == 0:
        return AnomalyReport(
            total_records=len(df),
            total_anomalies=0,
            anomaly_rate=0.0,
            severity_breakdown={},
            anomalies=[],
            column_anomaly_counts={},
            summary="No numeric columns available for anomaly detection.",
        )

    n = len(df)
    
    # We will build a matrix of votes (row, col) for each method
    # mapping: (row_idx, col) -> list of methods that flagged it
    flagged_cells: Dict[tuple(int, str), List[str]] = {}
    
    # Prepare standard statistics for explanations
    stats_cache: Dict[str, Dict[str, float]] = {}
    for col in cols:
        series = df[col].dropna()
        if not series.empty:
            stats_cache[col] = {
                "mean": float(series.mean()),
                "std": float(series.std()),
                "median": float(series.median()),
                "q1": float(series.quantile(0.25)),
                "q3": float(series.quantile(0.75)),
                "iqr": float(series.quantile(0.75) - series.quantile(0.25))
            }

    # ── 1. ISOLATION FOREST ──────────────────────────────────────────────────
    try:
        work = df[cols].copy()
        work = work.fillna(work.median())
        scaler = StandardScaler()
        scaled = scaler.fit_transform(work)
        
        clf = IsolationForest(contamination=min(contamination, 0.2), random_state=42, n_estimators=80, n_jobs=-1)
        preds = clf.fit_predict(scaled)
        
        for i in range(n):
            if preds[i] == -1:
                # Find columns that deviate most in this row
                row_vals = df.iloc[i]
                for col in cols:
                    val = row_vals.get(col)
                    if pd.isna(val) or col not in stats_cache:
                        continue
                    m = stats_cache[col]["mean"]
                    s = stats_cache[col]["std"]
                    if s > 0 and abs(float(val) - m) / s > 1.8:
                        key = (i, col)
                        if key not in flagged_cells:
                            flagged_cells[key] = []
                        flagged_cells[key].append("Isolation Forest")
    except Exception as e:
        logger.warning(f"Isolation forest anomaly detection step failed: {e}")

    # ── 2. Z-SCORE ───────────────────────────────────────────────────────────
    for col in cols:
        if col not in stats_cache or stats_cache[col]["std"] == 0:
            continue
        mean = stats_cache[col]["mean"]
        std = stats_cache[col]["std"]
        series = df[col]
        z_scores = (series - mean).abs() / std
        
        for i in z_scores[z_scores > 3.0].index:
            key = (i, col)
            if key not in flagged_cells:
                flagged_cells[key] = []
            flagged_cells[key].append("Z-Score")

    # ── 3. IQR ───────────────────────────────────────────────────────────────
    for col in cols:
        if col not in stats_cache:
            continue
        q1 = stats_cache[col]["q1"]
        q3 = stats_cache[col]["q3"]
        iqr = stats_cache[col]["iqr"]
        if iqr == 0:
            continue
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        series = df[col]
        outliers = series[(series < lower) | (series > upper)]
        
        for i in outliers.index:
            key = (i, col)
            if key not in flagged_cells:
                flagged_cells[key] = []
            flagged_cells[key].append("IQR")

    # ── 4. ROBUST MAD (Median Absolute Deviation) ───────────────────────────
    for col in cols:
        series = df[col]
        if col not in stats_cache:
            continue
        med = stats_cache[col]["median"]
        mad = np.median(np.abs(series.dropna() - med))
        scaled_mad = 1.4826 * mad
        if scaled_mad > 0:
            mod_z = (series - med).abs() / scaled_mad
            for i in mod_z[mod_z > 3.0].index:
                key = (i, col)
                if key not in flagged_cells:
                    flagged_cells[key] = []
                flagged_cells[key].append("Robust MAD")

    # ── 5. SEASONAL / ROLLING WINDOW DEVIATION ──────────────────────────────
    for col in cols:
        series = df[col].copy()
        # Compute 7-point rolling mean and rolling std (with index sorting as fallback for dates)
        roll_mean = series.rolling(window=7, min_periods=1).mean()
        roll_std = series.rolling(window=7, min_periods=1).std()
        
        # Fill standard deviation zeros
        roll_std = roll_std.replace(0.0, stats_cache[col]["std"] if col in stats_cache else 1.0).fillna(1.0)
        
        dev = (series - roll_mean).abs() / roll_std
        for i in dev[dev > 3.0].index:
            key = (i, col)
            if key not in flagged_cells:
                flagged_cells[key] = []
            flagged_cells[key].append("Seasonal Deviation")

    # ── 6. COMPILE CONSENSUS ANOMALIES ───────────────────────────────────────
    compiled_anomalies: List[DetectedAnomaly] = []
    
    # Find any categorical dimensions in df to diagnose causes
    cat_cols = [c for c in df.columns if c not in cols and not pd.api.types.is_numeric_dtype(df[c])][:3]

    for (row_idx, col), votes in flagged_cells.items():
        vote_count = len(votes)
        if vote_count == 0:
            continue
            
        score = vote_count / 5.0
        
        # Determine Severity based on consensus density
        if vote_count >= 4:
            severity = "critical"
            impact = "Severe variance outlier representing critical financial risk or pipeline ingestion error."
            rec = f"Immediately audit transaction log at index {row_idx}. Inspect upstream collection schema gates for '{col}'."
        elif vote_count == 3:
            severity = "high"
            impact = "Significant transaction anomaly detected. Likely to distort period-over-period aggregate metrics."
            rec = f"Review discount thresholds, tax applications, or fulfillment logs tied to '{col}'."
        elif vote_count == 2:
            severity = "medium"
            impact = "Moderate operational outlier. Standard variance deviation observed."
            rec = f"Monitor '{col}' trends. Flag if additional outliers cluster in this category."
        else:
            severity = "low"
            impact = "Minor variance outlier. Appears within standard tail distributions."
            rec = f"No immediate action required. Logged for baseline statistical history."

        val = df.at[row_idx, col]
        val_formatted = f"${float(val):,.2f}" if "revenue" in col.lower() or "sales" in col.lower() or "profit" in col.lower() else str(val)
        
        # Find likely cause from row dimensions
        cause_elements = []
        for cc in cat_cols:
            c_val = df.at[row_idx, cc]
            if not pd.isna(c_val):
                cause_elements.append(f"{cc}='{c_val}'")
        likely_cause = f"High variance row associated with: " + ", ".join(cause_elements) if cause_elements else f"Outlier numeric threshold reached in column '{col}'."
        
        # Expected range calculation
        expected_range = "N/A"
        if col in stats_cache:
            m = stats_cache[col]["mean"]
            s = stats_cache[col]["std"]
            expected_range = f"{m - 3*s:,.1f} to {m + 3*s:,.1f}"
            
        methods_str = ", ".join(set(votes))
        
        explanation = f"Value {val_formatted} in '{col}' flagged by {vote_count} methods ({methods_str}). Expected standard range is {expected_range}."

        # Collect other relevant values in the row to display context
        row_vals = {}
        for c in cols[:5]:
            if c != col:
                row_vals[c] = _safe_val(df.at[row_idx, c])
                
        compiled_anomalies.append(
            DetectedAnomaly(
                index=int(row_idx),
                severity=severity,
                score=round(score, 4),
                method=methods_str,
                columns_flagged=[col],
                values=row_vals,
                explanation=explanation,
                business_impact=impact,
                recommendation=rec,
                affected_kpi=col,
                likely_cause=likely_cause,
                expected_range=expected_range
            )
        )

    # Sort anomalies by score (consensus count) and absolute deviation descending
    compiled_anomalies.sort(key=lambda a: (a.score, a.index), reverse=True)
    
    severity_bd = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    col_counts: Dict[str, int] = {}
    for a in compiled_anomalies:
        severity_bd[a.severity] = severity_bd.get(a.severity, 0) + 1
        for c in a.columns_flagged:
            col_counts[c] = col_counts.get(c, 0) + 1

    # Keep only the top impactful anomalies to avoid flooding the user
    top_anomalies = compiled_anomalies[:40]

    return AnomalyReport(
        total_records=n,
        total_anomalies=len(compiled_anomalies),
        anomaly_rate=round(len(compiled_anomalies) / n * 100, 2) if n > 0 else 0.0,
        severity_breakdown=severity_bd,
        anomalies=top_anomalies,
        column_anomaly_counts=col_counts,
        summary=_generate_summary(len(compiled_anomalies), n, severity_bd),
    )


def _safe_val(v: Any) -> Any:
    """Convert value to JSON-safe type."""
    if isinstance(v, (np.integer, np.int64)):
        return int(v)
    if isinstance(v, (np.floating, np.float64)):
        return round(float(v), 2)
    if pd.isna(v):
        return None
    return v


def _generate_summary(n_anomalies: int, n_total: int, severity_bd: Dict[str, int]) -> str:
    rate = n_anomalies / n_total * 100 if n_total > 0 else 0
    critical = severity_bd.get("critical", 0)
    high = severity_bd.get("high", 0)

    if critical > 0:
        return f"Detected {n_anomalies} anomalies ({rate:.1f}%), including {critical} critical consensus alerts requiring immediate attention."
    elif high > 0:
        return f"Detected {n_anomalies} anomalies ({rate:.1f}%), with {high} high-severity items to investigate."
    elif n_anomalies > 0:
        return f"Detected {n_anomalies} anomalies ({rate:.1f}%). All are low-to-medium severity."
    return "No anomalies detected. Data appears within normal ranges."
