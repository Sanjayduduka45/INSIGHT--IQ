"""
InsightIQ — Schema Detector

Automatically detects column types, primary/foreign keys,
date columns, target variables, and semantic column roles.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class ColumnSchema:
    """Schema information for a single column."""

    name: str
    pandas_dtype: str
    semantic_type: str  # numeric, categorical, datetime, text, boolean, id
    role: str  # metric, dimension, date, id, target, text, unknown
    missing_count: int = 0
    missing_pct: float = 0.0
    unique_count: int = 0
    unique_pct: float = 0.0
    is_primary_key: bool = False
    is_foreign_key: bool = False
    sample_values: List[Any] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DatasetSchema:
    """Full schema for a dataset."""

    row_count: int
    column_count: int
    columns: List[ColumnSchema]
    date_columns: List[str] = field(default_factory=list)
    numeric_columns: List[str] = field(default_factory=list)
    categorical_columns: List[str] = field(default_factory=list)
    text_columns: List[str] = field(default_factory=list)
    id_columns: List[str] = field(default_factory=list)
    target_candidates: List[str] = field(default_factory=list)
    primary_key: Optional[str] = None
    memory_mb: float = 0.0


# ── Keyword maps for semantic detection ──────────────────────────────────

_ID_KEYWORDS = {"id", "key", "code", "index", "pk", "uuid", "guid", "number", "no", "num"}
_DATE_KEYWORDS = {
    "date",
    "time",
    "day",
    "month",
    "year",
    "period",
    "timestamp",
    "created",
    "updated",
    "modified",
}
_REVENUE_KEYWORDS = {
    "revenue",
    "sales",
    "income",
    "amount",
    "price",
    "value",
    "total",
    "fee",
    "turnover",
    "gross",
    "payment",
    "purchase",
}
_COST_KEYWORDS = {"cost", "expense", "spend", "budget", "expenditure", "charge"}
_PROFIT_KEYWORDS = {"profit", "margin", "earnings", "net", "gain"}
_QTY_KEYWORDS = {"quantity", "qty", "units", "items", "volume", "count", "orders"}
_RATE_KEYWORDS = {"rate", "ratio", "percentage", "pct", "score", "index"}
_GEO_KEYWORDS = {
    "region",
    "state",
    "city",
    "country",
    "area",
    "territory",
    "zone",
    "location",
    "address",
    "zip",
    "postal",
}
_CATEGORY_KEYWORDS = {
    "category",
    "type",
    "class",
    "group",
    "segment",
    "department",
    "division",
    "sector",
    "status",
    "level",
    "tier",
    "grade",
}
_NAME_KEYWORDS = {
    "name",
    "title",
    "label",
    "description",
    "product",
    "item",
    "customer",
    "employee",
    "patient",
    "student",
    "user",
    "company",
}


def detect_schema(df: pd.DataFrame) -> DatasetSchema:
    """Detect full schema from a DataFrame."""
    schema = DatasetSchema(
        row_count=len(df),
        column_count=len(df.columns),
        columns=[],
        memory_mb=df.memory_usage(deep=True).sum() / (1024 * 1024),
    )

    for col in df.columns:
        cs = _profile_column(df, col)
        schema.columns.append(cs)

        if cs.semantic_type == "datetime":
            schema.date_columns.append(col)
        elif cs.semantic_type == "numeric":
            schema.numeric_columns.append(col)
        elif cs.semantic_type == "categorical":
            schema.categorical_columns.append(col)
        elif cs.semantic_type == "text":
            schema.text_columns.append(col)

        if cs.is_primary_key:
            schema.id_columns.append(col)
            if schema.primary_key is None:
                schema.primary_key = col

    # Detect target candidates (binary/low-cardinality categoricals)
    for cs in schema.columns:
        if cs.semantic_type == "categorical" and 2 <= cs.unique_count <= 10:
            schema.target_candidates.append(cs.name)
        elif cs.semantic_type == "numeric" and cs.role == "metric":
            schema.target_candidates.append(cs.name)

    return schema


def _profile_column(df: pd.DataFrame, col: str) -> ColumnSchema:
    """Profile a single column."""
    series = df[col]
    n = len(df)
    cl = col.lower().replace(" ", "_").replace("-", "_")

    missing = int(series.isna().sum())
    unique = int(series.nunique())

    cs = ColumnSchema(
        name=col,
        pandas_dtype=str(series.dtype),
        semantic_type="unknown",
        role="unknown",
        missing_count=missing,
        missing_pct=round(missing / n * 100, 2) if n > 0 else 0,
        unique_count=unique,
        unique_pct=round(unique / n * 100, 2) if n > 0 else 0,
        sample_values=series.dropna().head(5).tolist(),
    )

    # ── Detect semantic type ─────────────────────────────────────
    if pd.api.types.is_datetime64_any_dtype(series):
        cs.semantic_type = "datetime"
        cs.role = "date"
    elif pd.api.types.is_bool_dtype(series):
        cs.semantic_type = "boolean"
        cs.role = "dimension"
    elif pd.api.types.is_numeric_dtype(series):
        cs.semantic_type = "numeric"
        cs.role = _detect_numeric_role(cl, unique, n)
        cs.stats = _numeric_stats(series)
    elif _is_parseable_date(series):
        cs.semantic_type = "datetime"
        cs.role = "date"
    elif pd.api.types.is_string_dtype(series) or pd.api.types.is_object_dtype(series):
        avg_len = series.dropna().astype(str).str.len().mean() if not series.dropna().empty else 0
        if avg_len > 100:
            cs.semantic_type = "text"
            cs.role = "text"
        else:
            cs.semantic_type = "categorical"
            cs.role = _detect_categorical_role(cl, unique, n)

    # ── Detect ID/key columns ────────────────────────────────────
    tokens = set(cl.split("_"))
    if tokens & _ID_KEYWORDS and cs.unique_pct > 90:
        cs.is_primary_key = True
        cs.role = "id"
    elif cs.unique_count == n and cs.semantic_type in ("numeric", "categorical"):
        cs.is_primary_key = True
        cs.role = "id"

    # ── Override role with keyword detection ─────────────────────
    if cs.semantic_type == "datetime" or any(kw in cl for kw in _DATE_KEYWORDS):
        if _is_parseable_date(series) or pd.api.types.is_datetime64_any_dtype(series):
            cs.role = "date"

    return cs


def _detect_numeric_role(cl: str, unique: int, n: int) -> str:
    """Determine if a numeric column is a metric or dimension."""
    tokens = set(cl.split("_"))
    if tokens & _ID_KEYWORDS:
        return "id"
    if any(
        kw in cl
        for kw in _REVENUE_KEYWORDS
        | _COST_KEYWORDS
        | _PROFIT_KEYWORDS
        | _QTY_KEYWORDS
        | _RATE_KEYWORDS
    ):
        return "metric"
    # Low cardinality numerics are likely dimensions (e.g., year, rating)
    if unique <= 20 and n > 100:
        return "dimension"
    return "metric"


def _detect_categorical_role(cl: str, unique: int, n: int) -> str:
    """Detect role for categorical columns."""
    if any(kw in cl for kw in _GEO_KEYWORDS):
        return "dimension"
    if any(kw in cl for kw in _CATEGORY_KEYWORDS):
        return "dimension"
    if any(kw in cl for kw in _NAME_KEYWORDS):
        return "dimension"
    return "dimension"


def _numeric_stats(series: pd.Series) -> dict:
    """Compute basic numeric statistics."""
    clean = series.dropna()
    if clean.empty:
        return {}
    return {
        "mean": round(float(clean.mean()), 4),
        "median": round(float(clean.median()), 4),
        "std": round(float(clean.std()), 4),
        "min": float(clean.min()),
        "max": float(clean.max()),
        "q25": float(clean.quantile(0.25)),
        "q75": float(clean.quantile(0.75)),
        "skew": round(float(clean.skew()), 4),
        "kurtosis": round(float(clean.kurtosis()), 4),
    }


def _is_parseable_date(series: pd.Series) -> bool:
    """Check if a string column contains parseable dates."""
    if pd.api.types.is_datetime64_any_dtype(series):
        return True
    if not (pd.api.types.is_string_dtype(series) or pd.api.types.is_object_dtype(series)):
        return False
    sample = series.dropna().head(20)
    if sample.empty:
        return False
    try:
        parsed = pd.to_datetime(sample, errors="coerce", format="mixed")
        success_rate = parsed.notna().mean()
        return success_rate > 0.8
    except Exception:
        return False
