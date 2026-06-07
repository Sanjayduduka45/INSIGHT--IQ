"""
InsightIQ — Forecasting API
"""

from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from api.datasets import get_dataset_store
from forecasting.engine import generate_forecast, detect_forecastable_columns

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/forecasting", tags=["forecasting"])


@router.get("/{dataset_id}/forecastable")
async def get_forecastable_columns(dataset_id: str):
    """Detect which columns can be forecasted."""
    ds = get_dataset_store().get(dataset_id)
    if not ds:
        raise HTTPException(404, "Dataset not found")

    schema = ds["schema"]
    df = ds["df"]

    # If no strict date column was detected, find fallback "date-like" columns
    if not schema.date_columns:
        date_like_keywords = [
            "date",
            "time",
            "created",
            "updated",
            "order",
            "transaction",
            "timestamp",
            "period",
        ]
        date_like_cols = [
            c.name for c in schema.columns if any(kw in c.name.lower() for kw in date_like_keywords)
        ]

        return {
            "dataset_id": dataset_id,
            "forecastable": [],
            "date_like_columns": date_like_cols,
            "message": "No valid time-series columns were found.",
        }

    from core.df_utils import get_analytic_numeric_cols
    analytic_nums = get_analytic_numeric_cols(df, schema)

    results = detect_forecastable_columns(df, schema.date_columns[0], analytic_nums)
    return {
        "dataset_id": dataset_id,
        "date_column": schema.date_columns[0],
        "forecastable": results,
        "date_like_columns": [],
    }


@router.get("/{dataset_id}/generate")
async def run_forecast(
    dataset_id: str,
    metric: Optional[str] = Query(None),
    date_column: Optional[str] = Query(None),
    horizons: str = Query("7,30,90"),
):
    """Generate forecasts for a metric."""
    ds = get_dataset_store().get(dataset_id)
    if not ds:
        raise HTTPException(404, "Dataset not found")

    schema = ds["schema"]
    df = ds["df"]

    # Use provided date column or fallback to detected
    target_date_col = date_column or (schema.date_columns[0] if schema.date_columns else None)

    if not target_date_col:
        raise HTTPException(400, "No date column detected or provided.")
    if target_date_col not in df.columns:
        raise HTTPException(400, f"Date column '{target_date_col}' not found in dataset.")

    from core.df_utils import get_analytic_numeric_cols
    analytic_nums = get_analytic_numeric_cols(df, schema)

    metric_col = metric or (analytic_nums[0] if analytic_nums else None)
    if not metric_col:
        raise HTTPException(400, "No numeric column available for forecasting.")
    if metric_col not in df.columns:
        raise HTTPException(400, f"Metric column '{metric_col}' not found in dataset.")

    horizon_list = [int(h.strip()) for h in horizons.split(",")]

    results = generate_forecast(
        df,
        target_date_col,
        metric_col,
        horizons=horizon_list,
    )

    return {
        "dataset_id": dataset_id,
        "metric": metric_col,
        "date_column": target_date_col,
        "forecasts": [asdict(r) for r in results],
    }
