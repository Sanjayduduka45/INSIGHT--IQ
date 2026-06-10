"""
InsightIQ — Trend Analysis Engine

Detects time-series trends, seasonal patterns, and generates
business interpretations for forecastable metrics.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


@dataclass
class TrendResult:
    """Result of trend analysis for a single metric."""

    column: str
    direction: str  # rising, falling, stable, volatile
    slope: float
    r_squared: float
    p_value: float
    is_significant: bool
    change_pct: float  # Overall % change
    interpretation: str
    data_points: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SeasonalPattern:
    """Detected seasonal pattern."""

    period: str  # daily, weekly, monthly, quarterly, yearly
    strength: float
    peak_period: str
    trough_period: str


def analyze_trends(
    df: pd.DataFrame,
    date_col: str,
    metric_cols: List[str],
    freq: str = "auto",
) -> List[TrendResult]:
    """Analyze trends for one or more metric columns over a date column."""
    results = []

    try:
        dates = pd.to_datetime(df[date_col], errors="coerce")
    except Exception:
        return results

    valid_mask = dates.notna()
    if valid_mask.sum() < 5:
        return results

    for col in metric_cols[:8]:  # Max 8 metrics
        if col not in df.columns:
            continue
        if not pd.api.types.is_numeric_dtype(df[col]):
            continue

        result = _analyze_single_trend(df[valid_mask], dates[valid_mask], col, freq)
        if result:
            results.append(result)

    return results


def _analyze_single_trend(
    df: pd.DataFrame,
    dates: pd.Series,
    col: str,
    freq: str,
) -> Optional[TrendResult]:
    """Analyze trend for a single column."""
    try:
        # Build time series
        ts_df = pd.DataFrame({"date": dates, "value": df[col]}).dropna()
        if len(ts_df) < 5:
            return None

        ts_df = ts_df.sort_values("date")

        # Auto-detect frequency and aggregate
        if freq == "auto":
            date_range = (ts_df["date"].max() - ts_df["date"].min()).days
            if date_range > 365:
                freq = "ME"
            elif date_range > 60:
                freq = "W"
            else:
                freq = "D"

        ts_agg = ts_df.set_index("date").resample(freq)["value"].mean().dropna()
        if len(ts_agg) < 3:
            return None

        # Linear regression
        x = np.arange(len(ts_agg))
        y = ts_agg.values
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        r_squared = r_value**2

        # Change percentage
        first_val = y[0] if y[0] != 0 else 1e-9
        change_pct = ((y[-1] - y[0]) / abs(first_val)) * 100

        # Direction
        if p_value < 0.05:
            direction = "rising" if slope > 0 else "falling"
        else:
            # Check volatility
            cv = np.std(y) / np.mean(y) if np.mean(y) != 0 else 0
            direction = "volatile" if cv > 0.3 else "stable"

        # Generate data points for charting
        data_points = [
            {"date": str(ts_agg.index[i].date()), "value": round(float(ts_agg.iloc[i]), 2)}
            for i in range(len(ts_agg))
        ]

        interpretation = _interpret_trend(col, direction, change_pct, r_squared)

        return TrendResult(
            column=col,
            direction=direction,
            slope=float(round(float(slope), 6)),
            r_squared=float(round(float(r_squared), 4)),
            p_value=float(round(float(p_value), 6)),
            is_significant=bool(p_value < 0.05),
            change_pct=float(round(float(change_pct), 2)),
            interpretation=interpretation,
            data_points=data_points,
        )
    except Exception as e:
        logger.warning("Trend analysis failed for %s: %s", col, e)
        return None


def _interpret_trend(col: str, direction: str, change_pct: float, r2: float) -> str:
    """Generate business-friendly trend interpretation."""
    strength = "strongly" if r2 > 0.7 else "moderately" if r2 > 0.3 else "weakly"

    if direction == "rising":
        return f"{col} is {strength} trending upward ({change_pct:+.1f}% change). This indicates sustained growth in this metric."
    elif direction == "falling":
        return f"{col} is {strength} declining ({change_pct:+.1f}% change). This warrants investigation into contributing factors."
    elif direction == "volatile":
        return f"{col} shows high volatility without a clear trend. Consider investigating seasonal or event-driven patterns."
    else:
        return f"{col} has remained relatively stable. No significant trend detected."


def compute_correlations(
    df: pd.DataFrame,
    numeric_cols: List[str],
    method: str = "pearson",
) -> Dict[str, Any]:
    """Compute correlation matrix and identify top correlations with business intelligence interpretations."""
    cols = [c for c in numeric_cols if c in df.columns][:20]  # Max 20 cols
    if len(cols) < 2:
        return {"matrix": {}, "top_correlations": [], "columns": cols}

    corr = df[cols].corr(method=method)

    # Extract top correlations
    top_pairs = []
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            val = corr.iloc[i, j]
            if not np.isnan(val):
                interpretation, action = _correlation_interpretation_and_action(cols[i], cols[j], float(val))
                top_pairs.append(
                    {
                        "col1": cols[i],
                        "col2": cols[j],
                        "correlation": round(float(val), 4),
                        "strength": _correlation_strength(abs(val)),
                        "interpretation": interpretation,
                        "action": action
                    }
                )

    top_pairs.sort(key=lambda x: abs(x["correlation"]), reverse=True)

    return {
        "matrix": {col: corr[col].round(4).to_dict() for col in cols},
        "top_correlations": top_pairs[:20],
        "columns": cols,
    }


def _correlation_strength(val: float) -> str:
    if val > 0.8:
        return "very strong"
    elif val > 0.6:
        return "strong"
    elif val > 0.4:
        return "moderate"
    elif val > 0.2:
        return "weak"
    return "negligible"


def _correlation_interpretation_and_action(col1: str, col2: str, corr_val: float) -> Tuple[str, str]:
    abs_corr = abs(corr_val)
    direction = "positive" if corr_val > 0 else "negative"
    strength = _correlation_strength(abs_corr)
    
    c1_l, c2_l = col1.lower(), col2.lower()
    
    # Sales/Revenue & Profit
    if (any(kw in c1_l for kw in ["sales", "revenue"]) and any(kw in c2_l for kw in ["profit", "margin"])) or \
       (any(kw in c2_l for kw in ["sales", "revenue"]) and any(kw in c1_l for kw in ["profit", "margin"])):
        if corr_val > 0.4:
            return (
                f"Sales and Profit show a {strength} positive correlation ({corr_val:.2f}). Higher sales volume generally translates to healthy profitability expansion.",
                "Accelerate conversion rates. Evaluate product margins to keep this coupling high."
            )
        else:
            return (
                f"Sales and Profit exhibit a weak correlation ({corr_val:.2f}). This indicates volume growth is diluted by discounting or operational overhead.",
                "Review pricing tiers and promotional discounts to protect product margin lines."
            )
            
    # Discount & Profit
    if "discount" in c1_l and any(kw in c2_l for kw in ["profit", "margin"]):
        if corr_val < -0.2:
            return (
                f"Discounts and Profit exhibit a negative correlation ({corr_val:.2f}), confirming promotional price reductions directly erode net margins.",
                "Set strict promotional ceilings. Focus on bundle incentives rather than raw item discounts."
            )

    if corr_val > 0.4:
        return (
            f"'{col1}' and '{col2}' show a {strength} positive relationship ({corr_val:.2f}). Their metrics scale in tandem, suggesting aligned performance channels.",
            f"Synchronize planning. Leverage growth in '{col1}' to drive secondary gains in '{col2}'."
        )
    elif corr_val < -0.4:
        return (
            f"'{col1}' and '{col2}' show a {strength} negative correlation ({corr_val:.2f}), indicating trade-offs or resource constraints.",
            f"Identify operational friction. Adjust supply or resource allocation to minimize '{col2}' dilution."
        )

    return (
        f"'{col1}' and '{col2}' show a weak correlation ({corr_val:.2f}), implying separate business drivers.",
        "Monitor baseline correlations. No structural co-dependency actions are required."
    )



def compute_distributions(
    df: pd.DataFrame,
    numeric_cols: List[str],
    n_bins: int = 30,
) -> List[Dict[str, Any]]:
    """Compute distribution summaries for numeric columns."""
    results = []
    for col in numeric_cols[:10]:
        if col not in df.columns:
            continue
        series = df[col].dropna()
        if series.empty:
            continue

        hist, edges = np.histogram(series, bins=min(n_bins, len(series)))
        results.append(
            {
                "column": col,
                "mean": round(float(series.mean()), 4),
                "median": round(float(series.median()), 4),
                "std": round(float(series.std()), 4),
                "skew": round(float(series.skew()), 4),
                "kurtosis": round(float(series.kurtosis()), 4),
                "min": float(series.min()),
                "max": float(series.max()),
                "histogram": {
                    "counts": hist.tolist(),
                    "edges": [round(float(e), 4) for e in edges],
                },
                "percentiles": {
                    "p5": float(series.quantile(0.05)),
                    "p25": float(series.quantile(0.25)),
                    "p50": float(series.quantile(0.50)),
                    "p75": float(series.quantile(0.75)),
                    "p95": float(series.quantile(0.95)),
                },
            }
        )

    return results


def compute_feature_importance(
    df: pd.DataFrame,
    target_col: str,
    feature_cols: List[str],
) -> List[Dict[str, Any]]:
    """Compute feature importance using RandomForest."""
    from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
    from sklearn.preprocessing import LabelEncoder

    features = [c for c in feature_cols if c in df.columns and c != target_col][:20]
    if not features or target_col not in df.columns:
        return []

    work_df = df[features + [target_col]].dropna()
    if len(work_df) < 20:
        return []

    # Encode categoricals
    le_map = {}
    for col in features:
        if not pd.api.types.is_numeric_dtype(work_df[col]):
            le = LabelEncoder()
            try:
                work_df[col] = le.fit_transform(work_df[col].astype(str))
                le_map[col] = le
            except Exception:
                work_df = work_df.drop(columns=[col])
                features.remove(col)

    if not features:
        return []

    X = work_df[features].values
    y = work_df[target_col]

    try:
        if pd.api.types.is_numeric_dtype(y):
            model = RandomForestRegressor(n_estimators=50, max_depth=8, random_state=42, n_jobs=-1)
        else:
            y = LabelEncoder().fit_transform(y.astype(str))
            model = RandomForestClassifier(n_estimators=50, max_depth=8, random_state=42, n_jobs=-1)

        model.fit(X, y)
        importances = model.feature_importances_

        results = [
            {"feature": features[i], "importance": round(float(importances[i]), 4)}
            for i in range(len(features))
        ]
        results.sort(key=lambda x: x["importance"], reverse=True)
        return results
    except Exception as e:
        logger.warning("Feature importance failed: %s", e)
        return []
