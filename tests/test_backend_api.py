from __future__ import annotations

import io
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Add apps/backend to sys.path
ROOT = Path(__file__).resolve().parents[1]
BACKEND_PATH = ROOT / "apps" / "backend"
if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))

from main import app
from api.datasets import get_dataset_store

client = TestClient(app)


@pytest.fixture
def mock_dataset():
    """Upload a mock dataset and return its ID."""
    csv_content = "date,revenue,units,category\n2026-01-01,100,5,A\n2026-01-02,120,6,B\n2026-01-03,110,5,A\n2026-01-04,130,7,B\n2026-01-05,500,2,C\n"
    file_payload = {"file": ("test.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}

    response = client.post("/api/datasets/upload", files=file_payload)
    assert response.status_code == 200
    data = response.json()
    dataset_id = data["dataset_id"]
    yield dataset_id

    # Cleanup
    client.delete(f"/api/datasets/{dataset_id}")


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["name"] == "InsightIQ API"


def test_dataset_upload_and_delete():
    csv_content = "date,revenue,category\n2026-01-01,100,A\n2026-01-02,150,B\n"
    file_payload = {"file": ("temp.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}

    response = client.post("/api/datasets/upload", files=file_payload)
    assert response.status_code == 200
    data = response.json()
    dataset_id = data["dataset_id"]
    assert data["rows"] == 2
    assert data["columns"] == 3

    # Get list
    response = client.get("/api/datasets/list")
    assert response.status_code == 200
    datasets = response.json()
    assert any(d["id"] == dataset_id for d in datasets)

    # Get preview
    response = client.get(f"/api/datasets/{dataset_id}/preview")
    assert response.status_code == 200
    preview = response.json()
    assert preview["total_rows"] == 2
    assert len(preview["data"]) == 2

    # Get metadata
    response = client.get(f"/api/datasets/{dataset_id}")
    assert response.status_code == 200
    meta = response.json()
    assert meta["rows"] == 2

    # Delete
    response = client.delete(f"/api/datasets/{dataset_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"


def test_analytics_overview(mock_dataset):
    response = client.get(f"/api/analytics/{mock_dataset}/overview")
    assert response.status_code == 200
    data = response.json()
    assert data["dataset_id"] == mock_dataset
    assert "health_scores" in data
    assert "kpis" in data
    assert "insights" in data
    assert "performers" in data
    assert "growth" in data
    assert "ai_recommendations" in data
    assert "root_cause_summary" in data


def test_analytics_kpis(mock_dataset):
    response = client.get(f"/api/analytics/{mock_dataset}/kpis")
    assert response.status_code == 200
    data = response.json()
    assert data["dataset_id"] == mock_dataset
    assert "kpis" in data


def test_analytics_trends(mock_dataset):
    response = client.get(f"/api/analytics/{mock_dataset}/trends")
    assert response.status_code == 200
    data = response.json()
    assert data["dataset_id"] == mock_dataset
    assert "trends" in data
    assert data["date_column"] == "date"


def test_analytics_correlations(mock_dataset):
    response = client.get(f"/api/analytics/{mock_dataset}/correlations")
    assert response.status_code == 200
    data = response.json()
    assert data["dataset_id"] == mock_dataset
    assert "top_correlations" in data


def test_analytics_distributions(mock_dataset):
    response = client.get(f"/api/analytics/{mock_dataset}/distributions")
    assert response.status_code == 200
    data = response.json()
    assert "distributions" in data


def test_analytics_feature_importance(mock_dataset):
    response = client.get(f"/api/analytics/{mock_dataset}/feature-importance?target=revenue")
    assert response.status_code == 200
    data = response.json()
    assert data["target"] == "revenue"
    assert "features" in data


def test_analytics_top_performers(mock_dataset):
    response = client.get(
        f"/api/analytics/{mock_dataset}/top-performers?dimension=category&metric=revenue"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["dimension"] == "category"
    assert data["metric"] == "revenue"
    assert len(data["items"]) > 0


def test_anomalies_detect(mock_dataset):
    response = client.get(f"/api/anomalies/{mock_dataset}/detect?contamination=0.05")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "anomalies" in data


def test_forecasting_generate(mock_dataset):
    response = client.get(f"/api/forecasting/{mock_dataset}/generate?metric=revenue&horizons=7,30")
    assert response.status_code == 200
    data = response.json()
    assert data["metric"] == "revenue"
    assert "forecasts" in data


def test_chat(mock_dataset):
    response = client.post(
        "/api/chat/", json={"dataset_id": mock_dataset, "message": "Summarize this dataset"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert len(data["suggested_questions"]) > 0


def test_export_pdf(mock_dataset):
    response = client.get(f"/api/export/{mock_dataset}/pdf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert len(response.content) > 0


def test_export_ppt(mock_dataset):
    response = client.get(f"/api/export/{mock_dataset}/ppt")
    assert response.status_code == 200
    assert (
        response.headers["content-type"]
        == "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )
    assert len(response.content) > 0


def test_export_csv(mock_dataset):
    response = client.get(f"/api/export/{mock_dataset}/csv")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert len(response.content) > 0


def test_charts_recommendation(mock_dataset):
    response = client.get(f"/api/analytics/{mock_dataset}/charts")
    assert response.status_code == 200
    data = response.json()
    assert "charts" in data
    assert len(data["charts"]) > 0


def test_categorical_only_dataset():
    """Upload a purely categorical dataset and verify robust response (no crash)."""
    csv_content = "category,status,priority\nA,Active,High\nB,Inactive,Low\nA,Active,Medium\n"
    file_payload = {"file": ("categorical.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}

    response = client.post("/api/datasets/upload", files=file_payload)
    assert response.status_code == 200
    dataset_id = response.json()["dataset_id"]

    # 1. KPIs endpoint - should generate fallback/categorical KPIs
    response = client.get(f"/api/analytics/{dataset_id}/kpis")
    assert response.status_code == 200
    kpis = response.json()["kpis"]
    assert len(kpis) > 0
    # There should be unique category counters or record count
    assert any("Unique" in k["name"] or "Records" in k["name"] for k in kpis)

    # 2. Charts endpoint - should output bar/pie charts for categorical variables
    response = client.get(f"/api/analytics/{dataset_id}/charts")
    assert response.status_code == 200
    charts = response.json()["charts"]
    assert len(charts) > 0
    assert any(c["type"] in ("bar", "pie") for c in charts)

    # 3. Overview endpoint - should generate insights and performers fallback
    response = client.get(f"/api/analytics/{dataset_id}/overview")
    assert response.status_code == 200
    data = response.json()
    assert "categorical_insights" in data
    assert len(data["categorical_insights"]) > 0

    # 4. Top performers endpoint fallback to record counts
    response = client.get(f"/api/analytics/{dataset_id}/top-performers?dimension=category")
    assert response.status_code == 200
    data = response.json()
    assert data["metric"] == "Record Count"
    assert data["items"][0]["sum"] == 2  # 'A' has 2 occurrences

    # Cleanup
    client.delete(f"/api/datasets/{dataset_id}")


def test_mixed_dataset_with_id_exclusion():
    """Upload a dataset with ID columns and ensure they are excluded from numeric analytics."""
    csv_content = "RowID,OrderID,value,category\n1,1001,15.5,A\n2,1002,12.0,B\n3,1003,18.0,A\n"
    file_payload = {"file": ("mixed_id.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}

    response = client.post("/api/datasets/upload", files=file_payload)
    assert response.status_code == 200
    dataset_id = response.json()["dataset_id"]

    # 1. Verify correlations matrix only contains 'value' and not RowID/OrderID
    response = client.get(f"/api/analytics/{dataset_id}/correlations")
    assert response.status_code == 200
    data = response.json()
    cols = data.get("columns", [])
    assert "value" in cols
    assert "RowID" not in cols
    assert "OrderID" not in cols

    # 2. Verify KPIs - Total RowID / OrderID should not be present
    response = client.get(f"/api/analytics/{dataset_id}/kpis")
    assert response.status_code == 200
    kpis = response.json()["kpis"]
    # We should not sum or mean RowID/OrderID as metric source
    assert not any("Total RowID" in k["name"] or "Total OrderID" in k["name"] for k in kpis)

    # 3. Verify Overview performers uses 'value' as primary metric, not RowID/OrderID
    response = client.get(f"/api/analytics/{dataset_id}/overview")
    assert response.status_code == 200
    data = response.json()
    assert data["performers"]["primary_metric"] == "value"

    # Cleanup
    client.delete(f"/api/datasets/{dataset_id}")
