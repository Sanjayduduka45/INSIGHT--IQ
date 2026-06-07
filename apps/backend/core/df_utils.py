"""
InsightIQ — DataFrame Utilities

Central helpers for safe column selection before analytics.
Every analytics operation (correlations, forecasting, anomaly detection,
KPI calculation) MUST use these helpers so that identifier columns
(OrderID, CustomerID, RowID, UUID, …) are never fed into numeric maths.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

import pandas as pd

logger = logging.getLogger(__name__)

# ── ID / non-analytic keyword signatures ─────────────────────────────────
_ID_TOKENS = {
    "id", "key", "code", "index", "pk", "uuid", "guid",
    "no", "num", "number", "ref", "record", "row", "seq",
    "invoice", "order", "transaction", "ticket", "sku",
    "serial", "barcode", "hash",
}


import re

def _col_tokens(col: str) -> set:
    """Normalise a column name and return its word tokens, splitting camelCase."""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', col)
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    return set(s2.replace("-", "_").replace(" ", "_").split("_"))


def _is_id_col(col: str, series: pd.Series) -> bool:
    """Return True if a column looks like an identifier that should not
    be used in arithmetic analytics (correlations, mean, sum, etc.)."""
    tokens = _col_tokens(col)
    if tokens & _ID_TOKENS:
        return True
    # Numeric columns where every value is unique and all are integers → likely a row-key
    if pd.api.types.is_numeric_dtype(series):
        n = len(series.dropna())
        if n > 10 and series.nunique() == n:
            try:
                if (series.dropna() % 1 == 0).all():
                    return True
            except Exception:
                pass
    return False


def _is_constant(series: pd.Series) -> bool:
    """Return True if a numeric column has zero variance (useless for analytics)."""
    clean = series.dropna()
    if clean.empty:
        return True
    try:
        return float(clean.std()) == 0.0
    except Exception:
        return True


# ── Public helpers ────────────────────────────────────────────────────────

def get_analytic_numeric_cols(df: pd.DataFrame, schema) -> List[str]:
    """Return numeric columns that are safe for arithmetic analytics.

    Excludes:
    - ID / key columns (detected by name tokens or full uniqueness)
    - Constant columns (std == 0)
    - Columns that are not truly numeric in the DataFrame
    """
    result = []
    for col in (schema.numeric_columns if schema else []):
        if col not in df.columns:
            continue
        series = df[col]
        if not pd.api.types.is_numeric_dtype(series):
            continue
        if _is_id_col(col, series):
            logger.debug("Excluding ID-like numeric column from analytics: %s", col)
            continue
        if _is_constant(series):
            logger.debug("Excluding constant numeric column from analytics: %s", col)
            continue
        result.append(col)
    return result


def get_categorical_cols(df: pd.DataFrame, schema) -> List[str]:
    """Return categorical / boolean columns that are safe for grouping.

    Excludes high-cardinality free-text columns (unique_pct > 90%).
    """
    result = []
    cat_cols = list(getattr(schema, "categorical_columns", []))
    for col in cat_cols:
        if col not in df.columns:
            continue
        series = df[col]
        n = len(series.dropna())
        if n == 0:
            continue
        # Skip if it looks like a unique identifier
        if _is_id_col(col, series):
            continue
        # Skip pure free-text (> 90 % unique values)
        if series.nunique() / n > 0.9:
            continue
        result.append(col)
    return result


def generate_categorical_insights(
    df: pd.DataFrame,
    schema,
    top_n: int = 10,
) -> List[Dict[str, Any]]:
    """Generate frequency/distribution insights for categorical columns.

    Returns a list of insight dicts, one per categorical column.
    """
    insights = []
    for col in get_categorical_cols(df, schema)[:8]:
        try:
            vc = df[col].dropna().astype(str).value_counts().head(top_n)
            if vc.empty:
                continue
            insights.append(
                {
                    "column": col,
                    "top_values": [
                        {"value": str(k), "count": int(v), "pct": round(int(v) / len(df) * 100, 1)}
                        for k, v in vc.items()
                    ],
                    "unique_count": int(df[col].nunique()),
                    "most_common": str(vc.index[0]),
                    "most_common_count": int(vc.iloc[0]),
                }
            )
        except Exception as e:
            logger.warning("Categorical insight failed for %s: %s", col, e)
    return insights
