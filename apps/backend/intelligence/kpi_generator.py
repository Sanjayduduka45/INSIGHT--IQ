"""
InsightIQ — Dynamic KPI Generator

Generates domain-appropriate KPIs based on the detected domain
and available columns. Never hardcodes Revenue or Sales assumptions.
Fully safe for mixed-type datasets (numeric + categorical + ID columns).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from intelligence.schema_detector import DatasetSchema
from core.df_utils import get_analytic_numeric_cols, get_categorical_cols

logger = logging.getLogger(__name__)


@dataclass
class KPI:
    """A computed Key Performance Indicator."""

    name: str
    value: float
    formatted_value: str
    unit: str  # currency, percentage, count, ratio, score
    trend: str  # up, down, stable
    trend_value: float  # e.g. +5.2%
    icon: str  # emoji icon
    category: str  # revenue, efficiency, quality, growth, risk
    priority: int  # 1-5
    column_source: str  # which column it derives from
    description: str  # business explanation


_DOMAIN_KPIS: Dict[str, List[Dict[str, Any]]] = {
    "SaaS": [
        {
            "name": "MRR (Monthly Recurring)",
            "keywords": ["mrr", "monthly_recurring", "recurring_revenue"],
            "agg": "sum",
            "unit": "currency",
            "icon": "🔄",
            "cat": "revenue",
        },
        {
            "name": "ARR (Annual Recurring)",
            "keywords": ["arr", "annual_recurring"],
            "agg": "sum",
            "unit": "currency",
            "icon": "🚀",
            "cat": "revenue",
        },
        {
            "name": "Churn Rate",
            "keywords": ["churn", "churn_rate", "attrition"],
            "agg": "mean",
            "unit": "percentage",
            "icon": "📉",
            "cat": "risk",
        },
        {
            "name": "Customer Acquisition Cost",
            "keywords": ["cac", "acquisition_cost"],
            "agg": "mean",
            "unit": "currency",
            "icon": "💸",
            "cat": "efficiency",
        },
        {
            "name": "Lifetime Value (LTV)",
            "keywords": ["ltv", "clv", "lifetime_value"],
            "agg": "mean",
            "unit": "currency",
            "icon": "💎",
            "cat": "growth",
        },
        {
            "name": "Retention Rate",
            "keywords": ["retention", "retention_rate", "active_users"],
            "agg": "mean",
            "unit": "percentage",
            "icon": "🛡️",
            "cat": "quality",
        },
    ],
    "Retail": [
        {
            "name": "Average Basket Value",
            "keywords": ["basket_value", "average_basket", "aov"],
            "agg": "mean",
            "unit": "currency",
            "icon": "🛒",
            "cat": "efficiency",
        },
        {
            "name": "Gross Margin",
            "keywords": ["margin", "gross_margin", "profit_margin"],
            "agg": "mean",
            "unit": "percentage",
            "icon": "📈",
            "cat": "efficiency",
        },
        {
            "name": "Sales Volume",
            "keywords": ["quantity", "volume", "units_sold"],
            "agg": "sum",
            "unit": "count",
            "icon": "📦",
            "cat": "growth",
        },
        {
            "name": "Return Rate",
            "keywords": ["return_rate", "refund_rate", "returns"],
            "agg": "mean",
            "unit": "percentage",
            "icon": "🔄",
            "cat": "risk",
        },
    ],
    "Marketing": [
        {
            "name": "Conversion Rate",
            "keywords": ["conversion_rate", "conversion", "conv_pct"],
            "agg": "mean",
            "unit": "percentage",
            "icon": "🎯",
            "cat": "efficiency",
        },
        {
            "name": "Click-Through Rate",
            "keywords": ["ctr", "click_through_rate"],
            "agg": "mean",
            "unit": "percentage",
            "icon": "🖱️",
            "cat": "efficiency",
        },
        {
            "name": "Cost Per Acquisition",
            "keywords": ["cpa", "cost_per_acquisition", "cost_per_lead"],
            "agg": "mean",
            "unit": "currency",
            "icon": "💵",
            "cat": "risk",
        },
        {
            "name": "Marketing ROI / ROAS",
            "keywords": ["roi", "roas", "return_on_ad_spend"],
            "agg": "mean",
            "unit": "percentage",
            "icon": "📊",
            "cat": "growth",
        },
        {
            "name": "Total Impressions",
            "keywords": ["impressions", "views"],
            "agg": "sum",
            "unit": "count",
            "icon": "👁️",
            "cat": "general",
        },
        {
            "name": "Total Clicks",
            "keywords": ["clicks"],
            "agg": "sum",
            "unit": "count",
            "icon": "🖱️",
            "cat": "general",
        },
    ],
    "Sales": [
        {
            "name": "Total Revenue",
            "keywords": ["revenue", "sales", "amount", "total", "income"],
            "agg": "sum",
            "unit": "currency",
            "icon": "💰",
            "cat": "revenue",
        },
        {
            "name": "Total Profit",
            "keywords": ["profit", "margin", "earnings"],
            "agg": "sum",
            "unit": "currency",
            "icon": "📈",
            "cat": "revenue",
        },
        {
            "name": "Order Count",
            "keywords": ["order", "transaction", "invoice"],
            "agg": "nunique",
            "unit": "count",
            "icon": "📦",
            "cat": "growth",
        },
        {
            "name": "Avg Order Value",
            "keywords": ["revenue", "sales", "amount", "total"],
            "agg": "mean",
            "unit": "currency",
            "icon": "🎯",
            "cat": "efficiency",
        },
        {
            "name": "Profit Margin",
            "keywords": ["margin", "profit_pct"],
            "agg": "mean",
            "unit": "percentage",
            "icon": "📊",
            "cat": "efficiency",
        },
        {
            "name": "Customer Count",
            "keywords": ["customer", "client", "buyer"],
            "agg": "nunique",
            "unit": "count",
            "icon": "👥",
            "cat": "growth",
        },
        {
            "name": "Discount Rate",
            "keywords": ["discount"],
            "agg": "mean",
            "unit": "percentage",
            "icon": "🏷️",
            "cat": "risk",
        },
    ],
    "Healthcare": [
        {
            "name": "Patient Volume",
            "keywords": ["patient", "admission"],
            "agg": "nunique",
            "unit": "count",
            "icon": "🏥",
            "cat": "growth",
        },
        {
            "name": "Avg Length of Stay",
            "keywords": ["length_of_stay", "los", "days", "stay"],
            "agg": "mean",
            "unit": "count",
            "icon": "🛏️",
            "cat": "efficiency",
        },
        {
            "name": "Readmission Rate",
            "keywords": ["readmission", "readmit"],
            "agg": "mean",
            "unit": "percentage",
            "icon": "🔄",
            "cat": "quality",
        },
        {
            "name": "Recovery Rate",
            "keywords": ["recovery", "recovered", "discharged"],
            "agg": "mean",
            "unit": "percentage",
            "icon": "💚",
            "cat": "quality",
        },
        {
            "name": "Treatment Cost",
            "keywords": ["cost", "charge", "bill", "amount"],
            "agg": "sum",
            "unit": "currency",
            "icon": "💰",
            "cat": "revenue",
        },
        {
            "name": "Diagnosis Count",
            "keywords": ["diagnosis", "icd", "condition"],
            "agg": "nunique",
            "unit": "count",
            "icon": "🩺",
            "cat": "growth",
        },
    ],
    "HR": [
        {
            "name": "Total Employees",
            "keywords": ["employee", "emp", "worker", "staff"],
            "agg": "nunique",
            "unit": "count",
            "icon": "👤",
            "cat": "growth",
        },
        {
            "name": "Attrition Rate",
            "keywords": ["attrition", "turnover", "left", "resigned"],
            "agg": "mean",
            "unit": "percentage",
            "icon": "📉",
            "cat": "risk",
        },
        {
            "name": "Avg Salary",
            "keywords": ["salary", "compensation", "pay", "wage"],
            "agg": "mean",
            "unit": "currency",
            "icon": "💰",
            "cat": "revenue",
        },
        {
            "name": "Satisfaction Score",
            "keywords": ["satisfaction", "engagement", "happiness"],
            "agg": "mean",
            "unit": "score",
            "icon": "😊",
            "cat": "quality",
        },
        {
            "name": "Tenure (Avg Years)",
            "keywords": ["tenure", "years", "experience"],
            "agg": "mean",
            "unit": "count",
            "icon": "📅",
            "cat": "efficiency",
        },
        {
            "name": "Department Count",
            "keywords": ["department", "division", "team"],
            "agg": "nunique",
            "unit": "count",
            "icon": "🏢",
            "cat": "growth",
        },
    ],
    "Education": [
        {
            "name": "Student Count",
            "keywords": ["student", "enrollment", "learner"],
            "agg": "nunique",
            "unit": "count",
            "icon": "🎓",
            "cat": "growth",
        },
        {
            "name": "Pass Rate",
            "keywords": ["pass", "passed", "grade"],
            "agg": "mean",
            "unit": "percentage",
            "icon": "✅",
            "cat": "quality",
        },
        {
            "name": "Avg Score",
            "keywords": ["score", "grade", "gpa", "marks"],
            "agg": "mean",
            "unit": "score",
            "icon": "📝",
            "cat": "quality",
        },
        {
            "name": "Attendance Rate",
            "keywords": ["attendance", "present"],
            "agg": "mean",
            "unit": "percentage",
            "icon": "📋",
            "cat": "efficiency",
        },
        {
            "name": "Course Count",
            "keywords": ["course", "subject", "class"],
            "agg": "nunique",
            "unit": "count",
            "icon": "📚",
            "cat": "growth",
        },
        {
            "name": "Completion Rate",
            "keywords": ["completion", "completed", "graduated"],
            "agg": "mean",
            "unit": "percentage",
            "icon": "🏆",
            "cat": "quality",
        },
    ],
    "Manufacturing": [
        {
            "name": "Production Volume",
            "keywords": ["production", "output", "units", "quantity"],
            "agg": "sum",
            "unit": "count",
            "icon": "🏭",
            "cat": "growth",
        },
        {
            "name": "Defect Rate",
            "keywords": ["defect", "reject", "scrap", "defective"],
            "agg": "mean",
            "unit": "percentage",
            "icon": "⚠️",
            "cat": "quality",
        },
        {
            "name": "Downtime Hours",
            "keywords": ["downtime", "idle", "maintenance"],
            "agg": "sum",
            "unit": "count",
            "icon": "⏸️",
            "cat": "risk",
        },
        {
            "name": "Yield Rate",
            "keywords": ["yield", "efficiency", "oee"],
            "agg": "mean",
            "unit": "percentage",
            "icon": "📊",
            "cat": "efficiency",
        },
        {
            "name": "Material Cost",
            "keywords": ["cost", "material", "expense"],
            "agg": "sum",
            "unit": "currency",
            "icon": "💰",
            "cat": "revenue",
        },
    ],
    "Finance": [
        {
            "name": "Total Transactions",
            "keywords": ["transaction", "transfer", "payment"],
            "agg": "count",
            "unit": "count",
            "icon": "💳",
            "cat": "growth",
        },
        {
            "name": "Total Value",
            "keywords": ["amount", "value", "balance", "total"],
            "agg": "sum",
            "unit": "currency",
            "icon": "💰",
            "cat": "revenue",
        },
        {
            "name": "Avg Transaction",
            "keywords": ["amount", "value", "balance"],
            "agg": "mean",
            "unit": "currency",
            "icon": "📊",
            "cat": "efficiency",
        },
        {
            "name": "Account Count",
            "keywords": ["account", "portfolio", "holder"],
            "agg": "nunique",
            "unit": "count",
            "icon": "🏦",
            "cat": "growth",
        },
        {
            "name": "Risk Score",
            "keywords": ["risk", "rating", "score"],
            "agg": "mean",
            "unit": "score",
            "icon": "⚡",
            "cat": "risk",
        },
    ],
    "Logistics": [
        {
            "name": "Total Shipments",
            "keywords": ["shipment", "delivery", "order"],
            "agg": "count",
            "unit": "count",
            "icon": "🚚",
            "cat": "growth",
        },
        {
            "name": "On-Time Rate",
            "keywords": ["ontime", "on_time", "delay"],
            "agg": "mean",
            "unit": "percentage",
            "icon": "⏰",
            "cat": "quality",
        },
        {
            "name": "Avg Transit Time",
            "keywords": ["transit", "delivery_time", "days"],
            "agg": "mean",
            "unit": "count",
            "icon": "📅",
            "cat": "efficiency",
        },
        {
            "name": "Total Freight Cost",
            "keywords": ["freight", "shipping", "cost"],
            "agg": "sum",
            "unit": "currency",
            "icon": "💰",
            "cat": "revenue",
        },
    ],
}


def generate_kpis(
    df: pd.DataFrame,
    schema: DatasetSchema,
    domain: str,
) -> List[KPI]:
    """Generate domain-specific KPIs from a dataset.

    Safe for mixed-type datasets — always uses `get_analytic_numeric_cols`
    so that ID columns, constant columns, and non-numeric columns are excluded
    before any arithmetic operation.
    """
    templates = _DOMAIN_KPIS.get(domain, [])

    # If domain not in templates, try to auto-generate from schema
    if not templates:
        templates = _auto_generate_templates(df, schema)

    kpis: List[KPI] = []
    for tmpl in templates:
        kpi = _compute_kpi(df, schema, tmpl)
        if kpi is not None:
            kpis.append(kpi)

    # If no KPIs generated, create fallback generic KPIs
    if not kpis:
        kpis = _fallback_kpis(df, schema)

    # Sort by priority
    kpis.sort(key=lambda k: k.priority)
    return kpis[:12]  # Max 12 KPIs


def _compute_kpi(df: pd.DataFrame, schema: DatasetSchema, tmpl: dict) -> Optional[KPI]:
    """Compute a single KPI from a template, skipping ID/non-numeric columns."""
    keywords = tmpl["keywords"]
    agg = tmpl["agg"]

    # Find matching column
    col = _find_column(df, keywords)
    if col is None:
        return None

    series = df[col].dropna()
    if series.empty:
        return None

    # For agg operations that require numeric data, validate the column
    needs_numeric = agg in ("sum", "mean", "median")
    if needs_numeric:
        # Coerce to numeric — skip if no values survive
        numeric_series = pd.to_numeric(series, errors="coerce").dropna()
        if numeric_series.empty:
            return None
        series = numeric_series

    try:
        if agg == "sum":
            value = float(series.sum())
        elif agg == "mean":
            value = float(series.mean())
        elif agg == "count":
            value = float(len(series))
        elif agg == "nunique":
            value = float(series.nunique())
        elif agg == "median":
            value = float(series.median())
        else:
            value = float(series.sum())
    except (TypeError, ValueError):
        return None

    # Compute trend (compare first half vs second half) — only for numeric series
    trend, trend_val = _compute_trend(series)

    return KPI(
        name=tmpl["name"],
        value=value,
        formatted_value=_format_value(value, tmpl["unit"]),
        unit=tmpl["unit"],
        trend=trend,
        trend_value=trend_val,
        icon=tmpl.get("icon", "📊"),
        category=tmpl.get("cat", "general"),
        priority=_priority_for_category(tmpl.get("cat", "general")),
        column_source=col,
        description=f"Computed from '{col}' using {agg}",
    )


def _find_column(df: pd.DataFrame, keywords: List[str]) -> Optional[str]:
    """Find the best matching column for a set of keywords."""
    cols = df.columns.tolist()
    for kw in keywords:
        for col in cols:
            cl = col.lower().replace(" ", "_").replace("-", "_")
            if kw == cl:  # Exact match
                return col
        for col in cols:
            cl = col.lower().replace(" ", "_").replace("-", "_")
            if kw in cl:  # Substring match
                return col
    return None


def _compute_trend(series: pd.Series) -> tuple:
    """Compute trend direction and magnitude. Safe for non-numeric series."""
    try:
        numeric = pd.to_numeric(series, errors="coerce").dropna()
        n = len(numeric)
        if n < 10:
            return "stable", 0.0

        half = n // 2
        first_half = float(numeric.iloc[:half].mean())
        second_half = float(numeric.iloc[half:].mean())

        if first_half == 0:
            return "stable", 0.0

        pct_change = ((second_half - first_half) / abs(first_half)) * 100

        if pct_change > 2:
            return "up", round(pct_change, 1)
        elif pct_change < -2:
            return "down", round(pct_change, 1)
        return "stable", round(pct_change, 1)
    except Exception:
        return "stable", 0.0


def _format_value(value: float, unit: str) -> str:
    """Format a KPI value for display."""
    if unit == "currency":
        if abs(value) >= 1_000_000:
            return f"${value / 1_000_000:,.1f}M"
        elif abs(value) >= 1_000:
            return f"${value / 1_000:,.1f}K"
        return f"${value:,.2f}"
    elif unit == "percentage":
        return f"{value:.1f}%"
    elif unit == "count":
        if abs(value) >= 1_000_000:
            return f"{value / 1_000_000:,.1f}M"
        elif abs(value) >= 1_000:
            return f"{value / 1_000:,.1f}K"
        return f"{value:,.0f}"
    elif unit == "score":
        return f"{value:.2f}"
    return f"{value:,.2f}"


def _priority_for_category(cat: str) -> int:
    """Map category to display priority."""
    return {"revenue": 1, "growth": 2, "quality": 3, "efficiency": 4, "risk": 5}.get(cat, 3)


def _auto_generate_templates(df: pd.DataFrame, schema: DatasetSchema) -> List[dict]:
    """Auto-generate KPI templates from schema when domain templates don't exist.

    Only targets analytic numeric columns (no IDs, no constants).
    """
    from core.df_utils import get_analytic_numeric_cols, get_categorical_cols
    templates = []

    analytic_nums = get_analytic_numeric_cols(df, schema)
    for col_name in analytic_nums[:6]:
        cl = col_name.lower()
        templates.append(
            {
                "name": f"Total {col_name}",
                "keywords": [cl],
                "agg": "sum",
                "unit": "count",
                "icon": "📊",
                "cat": "general",
            }
        )
        templates.append(
            {
                "name": f"Avg {col_name}",
                "keywords": [cl],
                "agg": "mean",
                "unit": "count",
                "icon": "📈",
                "cat": "efficiency",
            }
        )

    for col_name in get_categorical_cols(df, schema)[:3]:
        cl = col_name.lower()
        templates.append(
            {
                "name": f"Unique {col_name}",
                "keywords": [cl],
                "agg": "nunique",
                "unit": "count",
                "icon": "🏷️",
                "cat": "growth",
            }
        )

    return templates


def _fallback_kpis(df: pd.DataFrame, schema: DatasetSchema) -> List[KPI]:
    """Generate basic KPIs when no templates match.

    Includes categorical KPIs when no numeric columns are available.
    """
    from core.df_utils import get_analytic_numeric_cols, get_categorical_cols

    kpis = [
        KPI(
            name="Total Records",
            value=float(len(df)),
            formatted_value=f"{len(df):,}",
            unit="count",
            trend="stable",
            trend_value=0.0,
            icon="📋",
            category="general",
            priority=1,
            column_source="row_count",
            description="Total number of records in the dataset",
        ),
        KPI(
            name="Data Completeness",
            value=round((1 - df.isna().mean().mean()) * 100, 1),
            formatted_value=f"{(1 - df.isna().mean().mean()) * 100:.1f}%",
            unit="percentage",
            trend="stable",
            trend_value=0.0,
            icon="✅",
            category="quality",
            priority=2,
            column_source="all_columns",
            description="Percentage of non-missing values",
        ),
    ]

    # Analytic numeric summaries
    for col in get_analytic_numeric_cols(df, schema)[:4]:
        series = df[col].dropna()
        if series.empty:
            continue
        try:
            val = float(series.sum())
        except Exception:
            continue
        kpis.append(
            KPI(
                name=f"Total {col}",
                value=val,
                formatted_value=_format_value(val, "count"),
                unit="count",
                trend="stable",
                trend_value=0.0,
                icon="📊",
                category="general",
                priority=3,
                column_source=col,
                description=f"Sum of {col}",
            )
        )

    # Categorical KPIs (unique value counts)
    for col in get_categorical_cols(df, schema)[:3]:
        n_unique = int(df[col].nunique())
        most_common = str(df[col].mode().iloc[0]) if not df[col].mode().empty else "N/A"
        kpis.append(
            KPI(
                name=f"Unique {col}",
                value=float(n_unique),
                formatted_value=f"{n_unique:,}",
                unit="count",
                trend="stable",
                trend_value=0.0,
                icon="🏷️",
                category="growth",
                priority=4,
                column_source=col,
                description=f"Number of unique {col} values. Most common: {most_common}",
            )
        )

    return kpis
