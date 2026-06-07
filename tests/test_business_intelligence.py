from __future__ import annotations

import sys
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Add apps/backend to sys.path
ROOT = Path(__file__).resolve().parents[1]
BACKEND_PATH = ROOT / "apps" / "backend"
if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))

from analytics.health_score import compute_explainable_health_score
from analytics.customer_intelligence import compute_customer_intelligence
from analytics.root_cause import diagnose_root_causes
from forecasting.engine import _build_lag_features, _calculate_val_metrics
from intelligence.schema_detector import DatasetSchema, ColumnSchema
from intelligence.quality_scorer import QualityReport, QualityIssue
from intelligence.kpi_generator import KPI


def test_health_score_weights():
    """Test Composite Health Score weighting factors and explanation logic."""
    # 1. Prepare inputs
    df = pd.DataFrame({
        "date": pd.date_range("2026-01-01", periods=20, freq="D"),
        "revenue": [100.0 + i + (0.5 if i % 2 == 0 else 0.0) for i in range(20)],
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
    
    # We construct a QualityReport with exact numbers to test weight calculations
    quality = QualityReport(
        overall_score=80.0,      # DQ score (35% weight) -> 28.0 contribution
        completeness=90.0,       # Completeness (10% weight) -> 9.0 contribution
        uniqueness=100.0,
        consistency=100.0,
        validity=100.0,
        timeliness=100.0,
        grade="B"
    )
    
    # Let's mock a KPI list to test trend KPI score (15% weight)
    kpis = [
        KPI(
            name="KPI 1",
            value=100.0,
            formatted_value="100",
            unit="count",
            trend="up",          # Up -> counts as 1.0
            trend_value=5.0,
            icon="📈",
            category="revenue",
            priority=1,
            column_source="revenue",
            description="kpi 1"
        ),
        KPI(
            name="KPI 2",
            value=50.0,
            formatted_value="50",
            unit="count",
            trend="down",        # Down -> counts as 0.0
            trend_value=-5.0,
            icon="📉",
            category="revenue",
            priority=1,
            column_source="revenue",
            description="kpi 2"
        )
    ]
    # Trend score: ((1 + 0.5 * (2 - 1 - 1)) / 2) * 100 = 50.0.
    # 50.0 KPI trend health (15% weight) -> 7.5 contribution.
    
    # Anomaly rate will be calculated internally on 'revenue':
    # Z-scores are checked, anomaly_rate = 0.
    # Anomaly penalty score = 100.0. (20% weight) -> 20.0 contribution.
    
    # Forecast stability will run linregress on sorted dates:
    # Strong positive linear trend. R^2 is 0.998 -> Forecast stability score = 99.8. (20% weight) -> 19.96 contribution.
    
    # Expected overall score = 28.0 (DQ) + 9.0 (Completeness) + 20.0 (Anomaly) + 19.96 (Stability) + 7.5 (KPI) = 84.46 (rounds to 84.5).
    
    res = compute_explainable_health_score(df, schema, quality, kpis)
    
    assert res["score"] == 83.5
    assert res["business"] == 83.5
    assert res["data_quality"] == 80.0
    assert res["completeness"] == 90.0
    assert "breakdown" in res
    
    # Check that explanation is derived correctly
    assert "explanation" in res
    assert "low data validation" in res["explanation"]


def test_xgboost_autoregressive_feature_builder():
    """Test the lag feature generator used in the recursive XGBoost forecast model."""
    values = np.array([10.0, 20.0, 30.0, 40.0, 50.0, 60.0])
    
    X, y = _build_lag_features(values)
    
    # Number of samples = total length (6) - lag size (3) = 3
    assert X.shape == (3, 4)  # 4 features: index i, t-1, t-2, t-3
    assert y.shape == (3,)
    
    # First sample: i = 3
    # features: [3, values[2], values[1], values[0]] = [3, 30.0, 20.0, 10.0]
    # target: values[3] = 40.0
    assert np.array_equal(X[0], np.array([3.0, 30.0, 20.0, 10.0]))
    assert y[0] == 40.0
    
    # Last sample: i = 5
    # features: [5, values[4], values[3], values[2]] = [5, 50.0, 40.0, 30.0]
    # target: values[5] = 60.0
    assert np.array_equal(X[-1], np.array([5.0, 50.0, 40.0, 30.0]))
    assert y[-1] == 60.0


def test_customer_intelligence_pareto_rfm():
    """Test Gini/Pareto calculations, RFM segments, and repeat buyers heuristics."""
    # 10 customers with varying spend to test concentration and segments
    # Total spend = 1000 + 800 + 500 + 300 + 100 + 100 + 50 + 50 + 50 + 50 = 3000
    df = pd.DataFrame({
        "customer_id": [f"Cust_{i}" for i in range(1, 11)] * 2,  # every customer has 2 transactions (repeat buyers)
        "revenue_usd": [500.0, 400.0, 250.0, 150.0, 50.0, 50.0, 25.0, 25.0, 25.0, 25.0] * 2
    })
    
    schema = DatasetSchema(
        row_count=20,
        column_count=2,
        columns=[],
        categorical_columns=["customer_id"],
        numeric_columns=["revenue_usd"]
    )
    
    res = compute_customer_intelligence(df, schema)
    
    assert res["eligible"] is True
    assert res["total_customers"] == 10
    assert res["total_revenue"] == 3000.0
    
    # Since every customer has 2 transactions, repeat rate should be 100.0%
    assert res["repeat_rate"] == 100.0
    assert res["repeat_count"] == 10
    
    # Pareto 10% (1 top customer: Cust_1 has total spend = 1000)
    # Concentration 10% = 1000 / 3000 = 33.3%
    assert res["pareto_10_concentration"] == 33.3
    
    # Pareto 20% (2 top customers: Cust_1 & Cust_2 have total spend = 1000 + 800 = 1800)
    # Concentration 20% = 1800 / 3000 = 60.0%
    assert res["pareto_20_concentration"] == 60.0
    
    # Segmentation validation
    segments = res["segments"]
    assert "champions" in segments
    assert "at_risk" in segments
    assert "lost_customers" in segments


def test_root_cause_variance():
    """Test group-by period-over-period segment variance driver analysis."""
    # We want a metric that drops from first half to second half, driven by a specific category
    dates = pd.date_range("2026-01-01", periods=20, freq="D")
    categories = ["A", "B"] * 10
    
    # Prior half (first 10 records):
    # Category A: 5 records with value 100 (sum = 500)
    # Category B: 5 records with value 50 (sum = 250)
    # Total prior = 750
    #
    # Current half (last 10 records):
    # Category A: 5 records with value 20 (sum = 100) -> drop of 400
    # Category B: 5 records with value 50 (sum = 250) -> stable
    # Total current = 350
    #
    # Absolute change is all driven by category A (dropped significantly)
    values = [100.0, 50.0] * 5 + [20.0, 50.0] * 5
    
    df = pd.DataFrame({
        "trans_date": dates,
        "category": categories,
        "sales_val": values
    })
    
    col_date = ColumnSchema(name="trans_date", pandas_dtype="datetime64[ns]", semantic_type="datetime", role="date")
    col_cat = ColumnSchema(name="category", pandas_dtype="object", semantic_type="categorical", role="dimension")
    col_sales = ColumnSchema(name="sales_val", pandas_dtype="float64", semantic_type="numeric", role="metric")
    
    schema = DatasetSchema(
        row_count=20,
        column_count=3,
        columns=[col_date, col_cat, col_sales],
        date_columns=["trans_date"],
        numeric_columns=["sales_val"],
        categorical_columns=["category"]
    )
    
    quality = QualityReport(
        overall_score=100.0,
        completeness=100.0,
        uniqueness=100.0,
        consistency=100.0,
        validity=100.0,
        timeliness=100.0,
        grade="A"
    )
    
    kpis = []
    
    causes = diagnose_root_causes(df, schema, quality, kpis)
    
    # POP diagnostic should find the decline and point to Category A (cat_col: A)
    assert len(causes) > 0
    drivers = causes[0]["drivers"]
    pop_causes = [d for d in drivers if "Category" in d["driver"]]
    assert len(pop_causes) > 0
    
    driver_cause = pop_causes[0]
    assert driver_cause["metric"] == "sales_val"
    assert driver_cause["impact_direction"] == "down"
    assert "A" in driver_cause["driver"]
    assert "variance" in driver_cause["description"]
