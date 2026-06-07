"""
InsightIQ — Anomaly Detection API
"""

from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from api.datasets import get_dataset_store
from anomaly.detector import detect_anomalies

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/anomalies", tags=["anomalies"])


@router.get("/{dataset_id}/detect")
async def run_anomaly_detection(
    dataset_id: str,
    contamination: float = Query(0.05, ge=0.01, le=0.3),
    methods: Optional[str] = Query(None),
):
    """Run anomaly detection on a dataset."""
    ds = get_dataset_store().get(dataset_id)
    if not ds:
        raise HTTPException(404, "Dataset not found")

    df = ds["df"]
    schema = ds["schema"]
    method_list = methods.split(",") if methods else ["isolation_forest", "zscore", "iqr"]

    from core.df_utils import get_analytic_numeric_cols
    numeric_cols = get_analytic_numeric_cols(df, schema)

    report = detect_anomalies(
        df,
        numeric_cols,
        contamination=contamination,
        methods=method_list,
    )

    return {
        "dataset_id": dataset_id,
        "total_records": report.total_records,
        "total_anomalies": report.total_anomalies,
        "anomaly_rate": report.anomaly_rate,
        "severity_breakdown": report.severity_breakdown,
        "column_anomaly_counts": report.column_anomaly_counts,
        "summary": report.summary,
        "anomalies": [asdict(a) for a in report.anomalies[:50]],
    }
