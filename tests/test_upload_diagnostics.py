from __future__ import annotations

import io
import sys
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
BACKEND_PATH = ROOT / "backend"
if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))

from main import app
from core.settings import get_settings

client = TestClient(app)


def test_upload_size_limit_check():
    settings = get_settings()
    original_limit = settings.max_file_size_mb
    
    try:
        # Mock max file size to 0MB to force error
        settings.max_file_size_mb = 0
        csv_content = "date,revenue,units\n2026-01-01,100,5\n"
        file_payload = {"file": ("dataset_size_fail.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
        
        response = client.post("/api/datasets/upload", files=file_payload)
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "message" in data["detail"]
        assert "exceeds upload limit" in data["detail"]["message"].lower()
        assert data["detail"]["diagnostics"]["failure_stage"] == "size_check"
    finally:
        # Reset limit
        settings.max_file_size_mb = original_limit


def test_excel_extension_mismatch_xlsx_as_xls():
    # Write empty zip file bytes (mimicking XLSX structure) to .xls file
    xlsx_dummy = b"PK\x03\x04\x14\x00\x08\x08\x08\x00"
    file_payload = {"file": ("fake_xls.xls", io.BytesIO(xlsx_dummy), "application/vnd.ms-excel")}
    
    response = client.post("/api/datasets/upload", files=file_payload)
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Parser expected: XLSX" in data["detail"]["message"]
    assert data["detail"]["diagnostics"]["failure_stage"] == "parser_selection"


def test_cp1252_encoding_fallback_success():
    # Byte \x80 is the Euro sign in CP1252, but is invalid in UTF-8 on its own
    cp1252_content = b"date,revenue,notes\n2026-01-01,100,Special character: \x80\n"
    file_payload = {"file": ("cp1252_data.csv", io.BytesIO(cp1252_content), "text/csv")}
    
    response = client.post("/api/datasets/upload", files=file_payload)
    assert response.status_code == 200
    data = response.json()
    assert "diagnostics" in data
    # Encoding should reflect CP1252 with failed notice if default UTF-8 failed, or successfully CP1252
    assert "CP1252" in data["diagnostics"]["encoding"].upper()
    assert data["diagnostics"]["failure_stage"] is None
    
    # Clean up
    client.delete(f"/api/datasets/{data['dataset_id']}")


def test_malformed_csv_rows_check():
    # Inconsistent fields on row 2 (4 columns instead of 3)
    csv_content = "date,revenue,units\n2026-01-01,100,5\n2026-01-02,120,6,extra_field\n"
    file_payload = {"file": ("malformed_rows.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    
    response = client.post("/api/datasets/upload", files=file_payload)
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "malformed rows" in data["detail"]["message"].lower()
    assert data["detail"]["diagnostics"]["failure_stage"] == "parsing"
