"""Smoke tests for CI/CD and deployment verification."""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
backend_path = str(ROOT / "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)


def test_import_core_modules():
    modules = [
        "backend.main",
        "backend.core.settings",
        "backend.anomaly.detector",
        "backend.intelligence.quality_scorer",
        "backend.forecasting.engine",
        "backend.analytics.trends",
    ]
    for name in modules:
        importlib.import_module(name)


def test_settings_loads_successfully():
    from backend.core.settings import Settings

    s = Settings()
    assert s.app_name
    assert s.max_dataset_rows > 0


def test_anomaly_detector_runs():
    from backend.anomaly.detector import detect_anomalies

    df = pd.DataFrame({"value": [1.0, 2.0, 1.5, 100.0, 1.2, 1.8]})
    report = detect_anomalies(df, numeric_cols=["value"])
    assert report.total_records == 6
    assert report.total_anomalies >= 0
