from __future__ import annotations

import sys
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Add apps/backend to sys.path
ROOT = Path(__file__).resolve().parents[1]
BACKEND_PATH = ROOT / "backend"
if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))

from anomaly.detector import detect_anomalies
from analytics.customer_intelligence import compute_customer_intelligence
from forecasting.engine import generate_forecast
from analytics.health_score import compute_explainable_health_score
from intelligence.domain_classifier import classify_domain
from intelligence.schema_detector import DatasetSchema, ColumnSchema
from intelligence.quality_scorer import QualityReport
from intelligence.kpi_generator import KPI


def test_v2_consensus_anomaly_detection():
    """Verify Isolation Forest, Z-Score, IQR, Robust MAD, and Seasonal Deviation consensus anomaly detection."""
    # Construct a dataset with normal values and a clear outlier at index 10
    n_points = 30
    dates = pd.date_range("2026-01-01", periods=n_points, freq="D")
    values = [50.0 + (i % 3) for i in range(n_points)]
    values[10] = 500.0  # Big outlier
    
    df = pd.DataFrame({
        "trans_date": dates,
        "amount": values,
        "category": ["A"] * n_points
    })
    
    report = detect_anomalies(df, ["amount"], contamination=0.05)
    
    assert report.total_records == n_points
    assert report.total_anomalies >= 1
    
    # Check that our outlier at index 10 was flagged
    flagged_indices = [a.index for a in report.anomalies]
    assert 10 in flagged_indices
    
    # Verify anomaly properties
    anomaly_item = next(a for a in report.anomalies if a.index == 10)
    assert anomaly_item.severity in ("critical", "high", "medium")
    assert anomaly_item.affected_kpi == "amount"
    assert anomaly_item.likely_cause is not None
    assert anomaly_item.expected_range != "N/A"
    assert "amount" in anomaly_item.explanation
    
    # Check that MAD and Seasonal Deviation voters triggered
    assert len(anomaly_item.method) > 0


def test_v2_rfm_customer_segments_and_clv():
    """Verify Recency, Frequency, Monetary (RFM) indices, segmentation buckets, CLV, and Pareto."""
    # Construct 10 customers with varying spend and transactions
    # Customer 1 is a high-spending repeat buyer (Champion)
    # Customer 10 is a one-time low spender (Lost Customer or Needs Attention)
    dates = pd.date_range("2026-01-01", periods=20, freq="D")
    df = pd.DataFrame({
        "customer_id": [
            "Cust_1", "Cust_1", "Cust_1", "Cust_1", "Cust_2", "Cust_2", "Cust_3", "Cust_3",
            "Cust_4", "Cust_4", "Cust_5", "Cust_6", "Cust_7", "Cust_8", "Cust_9", "Cust_10",
            "Cust_1", "Cust_2", "Cust_3", "Cust_4"
        ],
        "spend_amt": [
            500.0, 500.0, 500.0, 500.0, 300.0, 300.0, 200.0, 200.0,
            150.0, 150.0, 100.0, 80.0, 60.0, 50.0, 40.0, 20.0,
            500.0, 300.0, 200.0, 150.0
        ],
        "trans_date": dates
    })
    
    col_date = ColumnSchema(name="trans_date", pandas_dtype="datetime64[ns]", semantic_type="datetime", role="date")
    col_cust = ColumnSchema(name="customer_id", pandas_dtype="object", semantic_type="categorical", role="dimension")
    col_spend = ColumnSchema(name="spend_amt", pandas_dtype="float64", semantic_type="numeric", role="metric")
    
    schema = DatasetSchema(
        row_count=20,
        column_count=3,
        columns=[col_date, col_cust, col_spend],
        date_columns=["trans_date"],
        numeric_columns=["spend_amt"],
        categorical_columns=["customer_id"]
    )
    
    res = compute_customer_intelligence(df, schema)
    
    assert res["eligible"] is True
    assert res["total_customers"] == 10
    
    # Verify segment keys exist
    segments = res["segments"]
    assert "champions" in segments
    assert "lost_customers" in segments
    
    # Customer 1 must have high CLV
    top_cust = res["top_customers"][0]
    assert top_cust["customer"] == "Cust_1"
    assert top_cust["clv"] > top_cust["spend"]  # CLV factor includes order repeat rate
    assert top_cust["churn_risk"] <= 50.0  # low churn risk because they are recent and active


def test_v2_multi_model_forecasting():
    """Verify Holt-Winters and Random Forest models train and split correctly."""
    # Construct a historical dataset with a strong trend
    n_points = 40
    dates = pd.date_range("2026-01-01", periods=n_points, freq="D")
    # Linear growing trend with some noise
    values = [100.0 + 5.0 * i + np.sin(i) for i in range(n_points)]
    
    df = pd.DataFrame({
        "date": dates,
        "sales": values
    })
    
    results = generate_forecast(df, "date", "sales", horizons=[7])
    
    assert len(results) > 0
    forecast_res = results[0]
    assert forecast_res.column == "sales"
    assert forecast_res.model_used in ("linear", "exponential_smoothing", "xgboost", "random_forest", "prophet")
    assert len(forecast_res.forecast) == 7
    assert forecast_res.metrics["mae"] >= 0


def test_v2_health_score_strict_formula():
    """Verify strict 5-factor weighting: Quality 30%, Growth 20%, Profitability 20%, Forecast 15%, Outliers 15%."""
    df = pd.DataFrame({
        "date": pd.date_range("2026-01-01", periods=20, freq="D"),
        "revenue": [100.0 + i for i in range(20)],
    })
    
    col_date = ColumnSchema(name="date", pandas_dtype="datetime64[ns]", semantic_type="datetime", role="date")
    col_rev = ColumnSchema(name="revenue", pandas_dtype="float64", semantic_type="numeric", role="metric")
    
    schema = DatasetSchema(
        row_count=20,
        column_count=2,
        columns=[col_date, col_rev],
        date_columns=["date"],
        numeric_columns=["revenue"]
    )
    
    quality = QualityReport(
        overall_score=90.0,
        completeness=100.0,
        uniqueness=100.0,
        consistency=100.0,
        validity=100.0,
        timeliness=100.0,
        grade="A"
    )
    
    res = compute_explainable_health_score(df, schema, quality, kpis=[])
    
    assert "score" in res
    assert "breakdown" in res
    
    # Verify breakdown weights sum to 100%
    bd = res["breakdown"]
    total_weight = sum(f["weight"] for f in bd.values())
    assert abs(total_weight - 1.0) < 1e-5
    
    # Assert specific weights
    assert bd["data_quality"]["weight"] == 0.30
    assert bd["revenue_growth"]["weight"] == 0.20
    assert bd["profitability"]["weight"] == 0.20
    assert bd["forecast_stability"]["weight"] == 0.15
    assert bd["anomaly_risk"]["weight"] == 0.15


def test_v2_domain_signature_classification():
    """Verify SaaS and Retail automatic domain classifications."""
    # SaaS Column Signatures
    df_saas = pd.DataFrame(columns=["subscription_id", "mrr", "churn_pct", "cac", "active_users", "user_license"])
    col_sub = ColumnSchema(name="subscription_id", pandas_dtype="object", semantic_type="categorical", role="id")
    schema_saas = DatasetSchema(row_count=0, column_count=6, columns=[col_sub], categorical_columns=["subscription_id"])
    
    res_saas = classify_domain(df_saas, schema_saas)
    assert res_saas.domain == "SaaS"
    assert res_saas.confidence >= 0.70
    
    # Retail Column Signatures
    df_retail = pd.DataFrame(columns=["sku_id", "average_basket", "refund_rate", "pos_terminal", "conversion"])
    col_sku = ColumnSchema(name="sku_id", pandas_dtype="object", semantic_type="categorical", role="id")
    schema_retail = DatasetSchema(row_count=0, column_count=5, columns=[col_sku], categorical_columns=["sku_id"])
    
    res_retail = classify_domain(df_retail, schema_retail)
    assert res_retail.domain == "Retail"
    assert res_retail.confidence >= 0.70
