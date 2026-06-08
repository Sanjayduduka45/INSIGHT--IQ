"""
InsightIQ — DataFrame Utilities

Central helpers for safe column selection before analytics.
Every analytics operation (correlations, forecasting, anomaly detection,
KPI calculation) MUST use these helpers so that identifier columns
(OrderID, CustomerID, RowID, UUID, …) are never fed into numeric maths.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List

import pandas as pd

logger = logging.getLogger(__name__)

# ── ID / non-analytic keyword signatures ─────────────────────────────────
# These tokens, when found in a column name, SUGGEST it might be an ID.
# But we now require BOTH name match AND data uniqueness to exclude.
_ID_TOKENS = {
    "id", "key", "code", "pk", "uuid", "guid",
    "ref", "seq", "invoice", "order", "transaction",
    "ticket", "sku", "serial", "barcode", "hash",
}

# ── Metric keyword whitelist ──────────────────────────────────────────────
# Columns matching these tokens should NEVER be treated as IDs,
# regardless of uniqueness. This is the critical fix.
_METRIC_TOKENS = {
    "revenue", "sales", "income", "amount", "price", "value", "total",
    "fee", "turnover", "gross", "payment", "purchase",
    "cost", "expense", "spend", "budget", "expenditure", "charge",
    "profit", "margin", "earnings", "net", "gain",
    "quantity", "qty", "units", "items", "volume", "count", "orders",
    "rate", "ratio", "percentage", "pct", "score", "rating",
    "weight", "height", "age", "salary", "wage", "tax",
    "discount", "tip", "balance", "deposit", "withdrawal",
    "temperature", "pressure", "speed", "distance", "area",
    "size", "length", "width", "depth",
}

# ── Dimension keyword whitelist ───────────────────────────────────────────
# Categorical columns matching these tokens should NOT be excluded
# even if they have high uniqueness.
_DIMENSION_TOKENS = {
    "category", "type", "class", "group", "segment", "department",
    "division", "sector", "status", "level", "tier", "grade",
    "region", "state", "city", "country", "area", "territory",
    "zone", "location", "name", "product", "brand", "model",
    "gender", "sex", "color", "colour", "size", "material",
    "channel", "source", "medium", "platform", "device",
    "priority", "severity", "risk",
}


def _col_tokens(col: str) -> set:
    """Normalise a column name and return its word tokens, splitting camelCase."""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', col)
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    return set(s2.replace("-", "_").replace(" ", "_").split("_"))


def _is_metric_col(col: str) -> bool:
    """Return True if a column name contains metric-related keywords."""
    tokens = _col_tokens(col)
    return bool(tokens & _METRIC_TOKENS)


def _is_dimension_col(col: str) -> bool:
    """Return True if a column name contains dimension-related keywords."""
    tokens = _col_tokens(col)
    return bool(tokens & _DIMENSION_TOKENS)


def _is_id_col(col: str, series: pd.Series) -> bool:
    """Return True if a column looks like an identifier that should not
    be used in arithmetic analytics (correlations, mean, sum, etc.).

    IMPORTANT: Requires BOTH name-based AND data-based evidence.
    Columns matching metric keywords are NEVER excluded.
    """
    # RULE 1: Metric columns are NEVER IDs
    if _is_metric_col(col):
        return False

    tokens = _col_tokens(col)
    has_id_name = bool(tokens & _ID_TOKENS)

    # RULE 2: If the column has an ID-like name AND all values are unique integers,
    # it is almost certainly an ID column.
    if has_id_name:
        if pd.api.types.is_numeric_dtype(series):
            n = len(series.dropna())
            if n > 10 and series.nunique() == n:
                try:
                    if (series.dropna() % 1 == 0).all():
                        return True
                except Exception:
                    pass
        # String columns with ID names and very high uniqueness are also IDs
        if pd.api.types.is_string_dtype(series) or pd.api.types.is_object_dtype(series):
            n = len(series.dropna())
            if n > 0 and series.nunique() / n > 0.95:
                return True

    # RULE 3: Columns explicitly named just "id" or ending with "_id" are IDs
    col_lower = col.lower().strip()
    if col_lower == "id" or col_lower.endswith("_id") or col_lower.endswith("id"):
        # But only if they look like identifiers (high uniqueness)
        n = len(series.dropna())
        if n > 0 and series.nunique() / n > 0.8:
            return True

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
    - ID / key columns (detected by BOTH name tokens AND full uniqueness)
    - Constant columns (std == 0)
    - Columns that are not truly numeric in the DataFrame

    SAFEGUARD: If the filtered result is empty but numeric columns exist
    in the schema, fall back to returning all non-constant numeric columns.
    """
    result = []
    all_numeric = []  # Track all valid numerics before ID filtering

    for col in (schema.numeric_columns if schema else []):
        if col not in df.columns:
            continue
        series = df[col]
        if not pd.api.types.is_numeric_dtype(series):
            continue
        if _is_constant(series):
            logger.debug("Excluding constant numeric column from analytics: %s", col)
            continue

        all_numeric.append(col)

        if _is_id_col(col, series):
            logger.debug("Excluding ID-like numeric column from analytics: %s", col)
            continue
        result.append(col)

    # SAFEGUARD: Never return empty if we have numeric columns available
    if not result and all_numeric:
        logger.warning(
            "All numeric columns were filtered as IDs. "
            "Falling back to all non-constant numeric columns: %s",
            all_numeric
        )
        return all_numeric

    return result


def get_categorical_cols(df: pd.DataFrame, schema) -> List[str]:
    """Return categorical / boolean columns that are safe for grouping.

    Excludes high-cardinality free-text columns (unique_pct > 95%)
    UNLESS the column name matches known dimension keywords.
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
        # Skip pure free-text (> 95% unique values) UNLESS it's a known dimension
        unique_ratio = series.nunique() / n
        if unique_ratio > 0.95 and not _is_dimension_col(col):
            logger.debug(
                "Excluding high-cardinality categorical column: %s (%.1f%% unique)",
                col, unique_ratio * 100
            )
            continue
        result.append(col)

    # SAFEGUARD: If no categoricals survived filtering but we have some in schema,
    # return the first few with lowest cardinality
    if not result and cat_cols:
        fallback = []
        for col in cat_cols:
            if col not in df.columns:
                continue
            series = df[col]
            n = len(series.dropna())
            if n == 0:
                continue
            fallback.append((col, series.nunique()))
        # Sort by cardinality (lowest first = most useful for grouping)
        fallback.sort(key=lambda x: x[1])
        result = [col for col, _ in fallback[:3]]
        if result:
            logger.warning(
                "All categorical columns were filtered. "
                "Falling back to lowest-cardinality columns: %s",
                result
            )

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
