"""
InsightIQ — Analytics API

Endpoints for KPIs, trends, correlations, distributions,
feature importance, and executive insights.
"""

from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from api.datasets import get_dataset_store
from analytics.trends import (
    analyze_trends,
    compute_correlations,
    compute_distributions,
    compute_feature_importance,
)
from intelligence.kpi_generator import KPI
from analytics.health_score import compute_explainable_health_score
from analytics.insights import generate_executive_report
from analytics.root_cause import diagnose_root_causes

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/{dataset_id}/kpis")
async def get_kpis(dataset_id: str):
    """Get computed KPIs for a dataset."""
    ds = get_dataset_store().get(dataset_id)
    if not ds:
        raise HTTPException(404, "Dataset not found")

    kpis: List[KPI] = ds.get("kpis", [])
    return {
        "dataset_id": dataset_id,
        "domain": ds["domain"].domain,
        "kpis": [asdict(k) for k in kpis],
    }


@router.get("/{dataset_id}/trends")
async def get_trends(
    dataset_id: str,
    date_col: Optional[str] = Query(None),
    metric_cols: Optional[str] = Query(None),
):
    """Analyze trends over time."""
    ds = get_dataset_store().get(dataset_id)
    if not ds:
        raise HTTPException(404, "Dataset not found")

    schema = ds["schema"]
    df = ds["df"]

    # Auto-select date column
    dc = date_col or (schema.date_columns[0] if schema.date_columns else None)
    if not dc:
        raise HTTPException(400, "No date column detected. Specify date_col parameter.")
    if dc not in df.columns:
        raise HTTPException(400, f"Date column '{dc}' not found in dataset.")

    # Auto-select metric columns
    if metric_cols:
        metrics = [m.strip() for m in metric_cols.split(",")]
        # Validate that specified metrics exist
        for m in metrics:
            if m not in df.columns:
                raise HTTPException(400, f"Metric column '{m}' not found in dataset.")
    else:
        from core.df_utils import get_analytic_numeric_cols
        metrics = get_analytic_numeric_cols(df, schema)[:6]

    results = analyze_trends(df, dc, metrics)
    return {
        "dataset_id": dataset_id,
        "date_column": dc,
        "trends": [asdict(r) for r in results],
    }


@router.get("/{dataset_id}/correlations")
async def get_correlations(
    dataset_id: str,
    method: str = Query("pearson"),
):
    """Compute correlation matrix."""
    ds = get_dataset_store().get(dataset_id)
    if not ds:
        raise HTTPException(404, "Dataset not found")

    from core.df_utils import get_analytic_numeric_cols
    numeric_cols = get_analytic_numeric_cols(ds["df"], ds["schema"])

    result = compute_correlations(
        ds["df"],
        numeric_cols,
        method=method,
    )
    return {"dataset_id": dataset_id, **result}


@router.get("/{dataset_id}/distributions")
async def get_distributions(dataset_id: str):
    """Compute distributions for numeric columns."""
    ds = get_dataset_store().get(dataset_id)
    if not ds:
        raise HTTPException(404, "Dataset not found")

    from core.df_utils import get_analytic_numeric_cols
    numeric_cols = get_analytic_numeric_cols(ds["df"], ds["schema"])

    results = compute_distributions(ds["df"], numeric_cols)
    return {"dataset_id": dataset_id, "distributions": results}


@router.get("/{dataset_id}/feature-importance")
async def get_feature_importance(
    dataset_id: str,
    target: Optional[str] = Query(None),
):
    """Compute feature importance using RandomForest."""
    ds = get_dataset_store().get(dataset_id)
    if not ds:
        raise HTTPException(404, "Dataset not found")

    schema = ds["schema"]
    df = ds["df"]
    target_col = target

    from core.df_utils import get_analytic_numeric_cols, get_categorical_cols
    analytic_nums = get_analytic_numeric_cols(df, schema)
    cat_cols = get_categorical_cols(df, schema)

    if not target_col:
        # Auto-select target
        if schema.target_candidates:
            target_col = schema.target_candidates[0]
        elif analytic_nums:
            target_col = analytic_nums[0]
        else:
            raise HTTPException(400, "No target column detected.")

    feature_cols = [
        c for c in analytic_nums + cat_cols if c != target_col
    ]

    results = compute_feature_importance(df, target_col, feature_cols)
    return {
        "dataset_id": dataset_id,
        "target": target_col,
        "features": results,
    }


from analytics.charts import recommend_charts
from intelligence.schema_detector import DatasetSchema


def _find_top_performers_for_keyword(
    df: pd.DataFrame,
    schema: DatasetSchema,
    keywords: List[str],
    metric: str,
    n: int = 10,
) -> Optional[List[Dict[str, Any]]]:
    from core.df_utils import get_categorical_cols
    col = None
    cat_cols = get_categorical_cols(df, schema)
    for kw in keywords:
        for c in cat_cols:
            if kw in c.lower():
                col = c
                break
        if col:
            break

    if not col and cat_cols:
        col = cat_cols[0]

    if not col:
        return None

    try:
        if metric in df.columns:
            grouped = df.groupby(col)[metric].sum().reset_index()
            grouped = grouped.sort_values(metric, ascending=False).head(n)
            return [
                {"name": str(row[col]), "value": float(row[metric])} for _, row in grouped.iterrows()
            ]
        else:
            # Fallback to counting records (for categorical-only or record count metric)
            grouped = df.groupby(col).size().reset_index(name="count")
            grouped = grouped.sort_values("count", ascending=False).head(n)
            return [
                {"name": str(row[col]), "value": float(row["count"])} for _, row in grouped.iterrows()
            ]
    except Exception:
        return None


def _compute_growth_metrics(df: pd.DataFrame, schema: DatasetSchema) -> Dict[str, Any]:
    from core.df_utils import get_analytic_numeric_cols
    analytic_nums = get_analytic_numeric_cols(df, schema)
    if not schema.date_columns or not analytic_nums:
        return {"growth_rate": 0.0, "status": "stable"}

    date_col = schema.date_columns[0]
    metric_col = analytic_nums[0]

    try:
        df_sorted = df.dropna(subset=[date_col, metric_col]).copy()
        df_sorted[date_col] = pd.to_datetime(df_sorted[date_col], errors="coerce")
        df_sorted = df_sorted.dropna(subset=[date_col]).sort_values(date_col)

        if len(df_sorted) < 4:
            return {"growth_rate": 0.0, "status": "stable"}

        half = len(df_sorted) // 2
        first_half = df_sorted.iloc[:half][metric_col].mean()
        second_half = df_sorted.iloc[half:][metric_col].mean()

        if first_half == 0:
            return {"growth_rate": 0.0, "status": "stable"}

        rate = ((second_half - first_half) / abs(first_half)) * 100
        return {
            "growth_rate": round(float(rate), 2),
            "status": "growth" if rate > 2 else "decline" if rate < -2 else "stable",
        }
    except Exception:
        return {"growth_rate": 0.0, "status": "stable"}


@router.get("/{dataset_id}/overview")
async def get_overview(dataset_id: str):
    """Get executive overview: KPIs, quality, domain, key insights."""
    ds = get_dataset_store().get(dataset_id)
    if not ds:
        raise HTTPException(404, "Dataset not found")

    schema = ds["schema"]
    quality = ds["quality"]
    domain = ds["domain"]
    kpis: List[KPI] = ds.get("kpis", [])
    df = ds["df"]

    # Business health score ( composite and explainable )
    health_explainable = compute_explainable_health_score(df, schema, quality, kpis)

    # Auto-generate insights
    insights = _generate_insights(df, schema, kpis, domain.domain)

    # Resolve top performers
    from core.df_utils import get_analytic_numeric_cols, generate_categorical_insights
    analytic_nums = get_analytic_numeric_cols(df, schema)
    primary_metric = analytic_nums[0] if analytic_nums else "records"
    performers = {
        "primary_metric": primary_metric,
        "products": _find_top_performers_for_keyword(
            df, schema, ["product", "item", "sku"], primary_metric
        ),
        "customers": _find_top_performers_for_keyword(
            df,
            schema,
            ["customer", "client", "member", "user", "patient", "student", "employee"],
            primary_metric,
        ),
        "categories": _find_top_performers_for_keyword(
            df, schema, ["category", "type", "class", "genre", "dept", "department"], primary_metric
        ),
        "regions": _find_top_performers_for_keyword(
            df, schema, ["region", "state", "country", "city", "location", "area"], primary_metric
        ),
    }

    # Growth metrics
    growth = _compute_growth_metrics(df, schema)

    # AI Recommendations
    ai_recs = []
    for k in kpis[:3]:
        if k.trend == "down":
            ai_recs.append(
                f"Investigate decline in {k.name} (currently {k.formatted_value}, down by {abs(k.trend_value)}%)."
            )
    if quality.overall_score < 85:
        ai_recs.append(
            "Run data cleansing and address missing records to improve decision-making fidelity."
        )
    if not ai_recs:
        ai_recs.append("Leverage the Forecast Center to model primary growth vectors.")
        ai_recs.append("Review correlation insights to identify key business drivers.")

    # Executive intelligence report
    executive_intel = generate_executive_report(df, schema, quality, kpis, domain.domain)

    # Root Cause Summary
    rc_summary = "All main indicators are performing within normal standard deviations."
    if quality.overall_score < 70:
        rc_summary = "Data completeness and consistency warnings represent the primary risk to reporting integrity."
    elif len(kpis) > 0:
        down_kpis = [k for k in kpis if k.trend == "down"]
        if down_kpis:
            rc_summary = f"Decline in {down_kpis[0].name} is likely correlated with temporal shifts or category variance."

    categorical_insights = generate_categorical_insights(df, schema)

    return {
        "dataset_id": dataset_id,
        "dataset_name": ds["name"],
        "domain": {
            "name": domain.domain,
            "confidence": domain.confidence,
        },
        "health_scores": health_explainable,
        "kpis": [asdict(k) for k in kpis[:8]],
        "insights": insights,
        "performers": performers,
        "growth": growth,
        "ai_recommendations": ai_recs,
        "executive_intelligence": executive_intel,
        "root_cause_summary": rc_summary,
        "categorical_insights": categorical_insights,
        "quick_stats": {
            "rows": schema.row_count,
            "columns": schema.column_count,
            "numeric_cols": len(schema.numeric_columns),
            "categorical_cols": len(schema.categorical_columns),
            "date_cols": len(schema.date_columns),
            "memory_mb": round(schema.memory_mb, 2),
        },
    }


@router.get("/{dataset_id}/root-cause")
async def get_root_cause(dataset_id: str):
    """Diagnose root causes for metric changes and data quality alerts."""
    ds = get_dataset_store().get(dataset_id)
    if not ds:
        raise HTTPException(404, "Dataset not found")

    df = ds["df"]
    schema = ds["schema"]
    quality = ds["quality"]
    kpis = ds.get("kpis", [])

    results = diagnose_root_causes(df, schema, quality, kpis)
    return {
        "dataset_id": dataset_id,
        "root_causes": results,
    }


@router.get("/{dataset_id}/customer-intelligence")
async def get_customer_intelligence(dataset_id: str):
    """Retrieve Pareto concentration, segment sizes, and transaction repeat loyalty metrics."""
    ds = get_dataset_store().get(dataset_id)
    if not ds:
        raise HTTPException(404, "Dataset not found")

    df = ds["df"]
    schema = ds["schema"]

    from analytics.customer_intelligence import compute_customer_intelligence
    results = compute_customer_intelligence(df, schema)
    return results


@router.get("/{dataset_id}/charts")
async def get_charts(dataset_id: str):
    """Get recommended charts for a dataset."""
    ds = get_dataset_store().get(dataset_id)
    if not ds:
        raise HTTPException(404, "Dataset not found")

    charts = recommend_charts(ds["df"], ds["schema"])
    return {
        "dataset_id": dataset_id,
        "charts": charts,
    }


@router.get("/{dataset_id}/top-performers")
async def get_top_performers(
    dataset_id: str,
    dimension: Optional[str] = Query(None),
    metric: Optional[str] = Query(None),
    n: int = Query(10),
):
    """Get top N performers for a dimension by a metric."""
    ds = get_dataset_store().get(dataset_id)
    if not ds:
        raise HTTPException(404, "Dataset not found")

    df = ds["df"]
    schema = ds["schema"]

    from core.df_utils import get_analytic_numeric_cols, get_categorical_cols
    cat_cols = get_categorical_cols(df, schema)
    analytic_nums = get_analytic_numeric_cols(df, schema)

    dim = dimension or (cat_cols[0] if cat_cols else None)
    met = metric or (analytic_nums[0] if analytic_nums else None)

    if not dim:
        raise HTTPException(400, "Need at least one categorical column.")

    if not met:
        # Fallback to counting occurrences of the dimension (record count)
        grouped = df.groupby(dim).size().reset_index(name="sum")
        grouped["mean"] = 1.0
        grouped["count"] = grouped["sum"]
        grouped = grouped.sort_values("sum", ascending=False).head(n)
        return {
            "dimension": dim,
            "metric": "Record Count",
            "items": grouped.rename(columns={dim: "name"}).to_dict(orient="records"),
        }

    grouped = df.groupby(dim)[met].agg(["sum", "mean", "count"]).reset_index()
    grouped = grouped.sort_values("sum", ascending=False).head(n)

    return {
        "dimension": dim,
        "metric": met,
        "items": grouped.rename(columns={dim: "name"}).to_dict(orient="records"),
    }


def _compute_health_score(kpis: List[KPI], quality: float) -> float:
    """Composite business health score."""
    if not kpis:
        return quality

    # Weight: up trends are positive, down trends are negative
    trend_scores = []
    for kpi in kpis:
        if kpi.trend == "up":
            trend_scores.append(80 + min(abs(kpi.trend_value), 20))
        elif kpi.trend == "down":
            trend_scores.append(max(50 - abs(kpi.trend_value), 20))
        else:
            trend_scores.append(70)

    avg_trend = sum(trend_scores) / len(trend_scores)
    return round(avg_trend * 0.6 + quality * 0.4, 1)


def _generate_insights(df, schema, kpis, domain) -> List[Dict[str, Any]]:
    """Auto-generate top insights."""
    insights = []

    # Insight 1: Strongest KPI trend
    trending_kpis = [k for k in kpis if k.trend in ("up", "down")]
    if trending_kpis:
        best = max(trending_kpis, key=lambda k: abs(k.trend_value))
        direction = "increased" if best.trend == "up" else "decreased"
        insights.append(
            {
                "type": "trend",
                "title": f"{best.name} {direction} by {abs(best.trend_value):.1f}%",
                "description": f"Your {best.name.lower()} has {direction} significantly. This is {'positive' if best.trend == 'up' else 'concerning'} for business performance.",
                "severity": "positive" if best.trend == "up" else "warning",
                "priority": 1,
            }
        )

    # Insight 2: Data quality
    if schema:
        missing_pct = df.isna().mean().mean() * 100
        if missing_pct > 5:
            insights.append(
                {
                    "type": "quality",
                    "title": f"{missing_pct:.1f}% data is missing",
                    "description": "Significant missing data may affect analysis accuracy. Consider data imputation or review data collection processes.",
                    "severity": "warning" if missing_pct > 15 else "info",
                    "priority": 2,
                }
            )

    # Insight 3: Top category
    from core.df_utils import get_categorical_cols, get_analytic_numeric_cols
    cat_cols = get_categorical_cols(df, schema)
    analytic_nums = get_analytic_numeric_cols(df, schema)
    if cat_cols and analytic_nums:
        try:
            cat_col = cat_cols[0]
            num_col = analytic_nums[0]
            top = df.groupby(cat_col)[num_col].sum().idxmax()
            top_val = df.groupby(cat_col)[num_col].sum().max()
            insights.append(
                {
                    "type": "highlight",
                    "title": f"Top {cat_col}: {top}",
                    "description": f"'{top}' leads in {num_col} with a total of {top_val:,.0f}.",
                    "severity": "positive",
                    "priority": 3,
                }
            )
        except Exception:
            pass

    return insights[:10]
