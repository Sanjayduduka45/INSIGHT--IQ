from __future__ import annotations

import io
import sys
import zipfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Add apps/backend to sys.path
ROOT = Path(__file__).resolve().parents[1]
BACKEND_PATH = ROOT / "backend"
if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))

from main import app
from api.datasets import get_dataset_store

client = TestClient(app)


def test_zip_file_upload():
    # 1. Create a zip archive in memory containing a valid CSV file
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        csv_content = "date,revenue,units,category\n2026-01-01,100,5,A\n2026-01-02,120,6,B\n"
        zip_file.writestr("sales.csv", csv_content)
    
    zip_buffer.seek(0)
    file_payload = {"file": ("dataset.zip", zip_buffer, "application/zip")}

    # 2. Upload and assert success
    response = client.post("/api/datasets/upload", files=file_payload)
    assert response.status_code == 200
    data = response.json()
    dataset_id = data["dataset_id"]
    assert data["rows"] == 2
    assert data["columns"] == 4

    # Cleanup
    client.delete(f"/api/datasets/{dataset_id}")


def test_semicolon_delimited_csv_upload():
    # Semicolon separator with formatting commas
    csv_content = "date;revenue;units;category\n2026-01-01;100;5;A\n2026-01-02;120;6;B\n"
    file_payload = {"file": ("data_semicolon.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}

    response = client.post("/api/datasets/upload", files=file_payload)
    assert response.status_code == 200
    data = response.json()
    dataset_id = data["dataset_id"]
    assert data["rows"] == 2
    assert data["columns"] == 4

    # Cleanup
    client.delete(f"/api/datasets/{dataset_id}")


def test_currency_and_percentage_cleaning():
    # Test column values like "$1,200.50", "15.5%", and parenthetical negative "(500)"
    csv_content = (
        "date,revenue,growth,loss,category\n"
        '2026-01-01,"$1,200.50",15.5%,(500),A\n'
        '2026-01-02,"$1,500.00",10.0%,(200),B\n'
    )
    file_payload = {"file": ("formatted_data.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}

    response = client.post("/api/datasets/upload", files=file_payload)
    assert response.status_code == 200
    data = response.json()
    dataset_id = data["dataset_id"]
    assert data["rows"] == 2

    # Get preview to verify type conversion and values
    response_preview = client.get(f"/api/datasets/{dataset_id}/preview")
    assert response_preview.status_code == 200
    preview_data = response_preview.json()["data"]

    # Verify conversions:
    # "$1,200.50" -> 1200.5
    # "15.5%" -> 0.155
    # "(500)" -> -500.0
    assert float(preview_data[0]["revenue"]) == 1200.5
    assert float(preview_data[0]["growth"]) == 0.155
    assert float(preview_data[0]["loss"]) == -500.0

    # Cleanup
    client.delete(f"/api/datasets/{dataset_id}")


def test_forecasting_engine_resilience():
    # Test uploading a small dataset and querying forecast with invalid columns
    csv_content = "date,revenue,units\n2026-01-01,100,5\n2026-01-02,120,6\n"
    file_payload = {"file": ("test_forecast.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}

    response = client.post("/api/datasets/upload", files=file_payload)
    data = response.json()
    dataset_id = data["dataset_id"]

    # Query with a non-existent metric column
    response_forecast = client.get(
        f"/api/forecasting/{dataset_id}/generate?metric=invalid_col&date_column=date"
    )
    assert response_forecast.status_code == 400
    assert "No numeric column" in response_forecast.json()["detail"] or "invalid" in response_forecast.json()["detail"].lower()

    # Query with a non-existent date column
    response_forecast = client.get(
        f"/api/forecasting/{dataset_id}/generate?metric=revenue&date_column=invalid_date"
    )
    assert response_forecast.status_code == 400

    # Cleanup
    client.delete(f"/api/datasets/{dataset_id}")


def test_cold_start_recovery():
    # 1. Upload a dataset
    csv_content = "date,revenue,units\n2026-01-01,100,5\n2026-01-02,120,6\n2026-01-03,110,7\n"
    file_payload = {"file": ("cold_start_test.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}

    response = client.post("/api/datasets/upload", files=file_payload)
    assert response.status_code == 200
    dataset_id = response.json()["dataset_id"]

    # Verify it was cached in memory
    from api.datasets import _datasets
    assert dataset_id in _datasets

    # 2. Simulate server restart by clearing in-memory cache
    del _datasets[dataset_id]
    assert dataset_id not in _datasets

    # 3. Retrieve the dataset metadata - this should trigger reload from Parquet cache file
    response_get = client.get(f"/api/datasets/{dataset_id}")
    assert response_get.status_code == 200
    metadata = response_get.json()
    assert metadata["name"] == "cold_start_test.csv"
    assert metadata["rows"] == 3

    # Confirm it was re-cached back into memory
    assert dataset_id in _datasets

    # 4. Clean up
    client.delete(f"/api/datasets/{dataset_id}")
    assert dataset_id not in _datasets

