"""
InsightIQ — Forecasting Engine V2

Multi-model forecasting with automatic model selection.
Supports: Linear Trend, XGBoost, Random Forest, Exponential Smoothing (Holt-Winters), and Prophet.
Evaluates models on a Train/Validation split (80/20) and selects the best by MAE.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


@dataclass
class ForecastPoint:
    """A single forecast data point."""
    date: str
    value: float
    lower_bound: float
    upper_bound: float
    is_forecast: bool = True


@dataclass
class ForecastResult:
    """Complete forecast for a metric."""
    column: str
    model_used: str
    horizon_days: int
    historical: List[ForecastPoint]
    forecast: List[ForecastPoint]
    metrics: Dict[str, float]  # MAE, RMSE, MAPE, R²
    interpretation: str
    trend_direction: str
    confidence_level: float


def generate_forecast(
    df: pd.DataFrame,
    date_col: str,
    metric_col: str,
    horizons: Optional[List[int]] = None,
) -> List[ForecastResult]:
    """Generate forecasts at multiple horizons by selecting the best fit model."""
    if horizons is None:
        horizons = [7, 30, 90, 365]

    if date_col not in df.columns or metric_col not in df.columns:
        logger.warning(f"Forecasting aborted: {date_col} or {metric_col} not in DataFrame columns.")
        return []

    try:
        dates = pd.to_datetime(df[date_col], errors="coerce")
    except Exception as e:
        logger.warning(f"Forecasting aborted: Failed to parse date column '{date_col}': {e}")
        return []

    try:
        metric_series = pd.to_numeric(df[metric_col], errors="coerce")
    except Exception as e:
        logger.warning(f"Forecasting aborted: Metric column '{metric_col}' is not numeric: {e}")
        return []

    valid = dates.notna() & metric_series.notna()
    ts_df = (
        pd.DataFrame(
            {
                "date": dates[valid],
                "value": metric_series[valid].astype(float),
            }
        )
        .sort_values("date")
        .reset_index(drop=True)
    )

    if len(ts_df) < 10:
        return []

    results = []
    for horizon in horizons:
        result = _run_multi_model_selection_and_forecast(ts_df, metric_col, horizon)
        if result:
            results.append(result)

    return results


def _detect_frequency_and_offset(ts_df: pd.DataFrame) -> Tuple[str, Any]:
    """Detects frequency of datetime series and returns pandas resampling frequency and DateOffset."""
    try:
        inferred = pd.infer_freq(ts_df["date"].head(50))
        if inferred:
            if inferred.startswith("Q"):
                return "QE", pd.DateOffset(months=3)
            if inferred.startswith("Y") or inferred.startswith("A"):
                return "YE", pd.DateOffset(years=1)
            if inferred.startswith("M"):
                return "ME", pd.DateOffset(months=1)
            if inferred.startswith("W"):
                return "W", pd.DateOffset(weeks=1)
            if inferred.startswith("D"):
                return "D", pd.DateOffset(days=1)
    except Exception:
        pass

    # Fallback heuristic based on date range and count
    date_range = (ts_df["date"].max() - ts_df["date"].min()).days
    n_points = len(ts_df["date"].unique())
    if n_points < 3:
        return "D", pd.DateOffset(days=1)

    avg_gap = date_range / (n_points - 1)
    if avg_gap >= 360:
        return "YE", pd.DateOffset(years=1)
    elif avg_gap >= 80:
        return "QE", pd.DateOffset(months=3)
    elif avg_gap >= 28:
        return "ME", pd.DateOffset(months=1)
    elif avg_gap >= 6:
        return "W", pd.DateOffset(weeks=1)
    else:
        return "D", pd.DateOffset(days=1)


def _run_multi_model_selection_and_forecast(
    ts_df: pd.DataFrame,
    col_name: str,
    horizon: int
) -> Optional[ForecastResult]:
    """Evaluates Linear, XGBoost, Random Forest, Holt-Winters, and Prophet on 80/20 train/validation split."""
    try:
        freq, delta = _detect_frequency_and_offset(ts_df)
        
        # Aggregate to detected frequency
        ts = ts_df.set_index("date").resample(freq)["value"].mean().dropna()
        if len(ts) < 8:
            return None

        # ── 1. SPLIT DATA FOR VALIDATION ──────────────────────────────────────
        val_size = max(2, int(len(ts) * 0.2))
        train_ts = ts.iloc[:-val_size]
        val_ts = ts.iloc[-val_size:]
        
        # Candidate model evaluations
        candidates = {}
        
        # Candidate A: Linear Trend
        candidates["linear"] = _evaluate_linear(train_ts, val_ts)
        
        # Candidate B: XGBoost
        candidates["xgboost"] = _evaluate_xgboost(train_ts, val_ts)

        # Candidate C: Random Forest
        candidates["random_forest"] = _evaluate_random_forest(train_ts, val_ts)

        # Candidate D: Exponential Smoothing (Holt-Winters)
        candidates["exponential_smoothing"] = _evaluate_exponential_smoothing(train_ts, val_ts)
        
        # Candidate E: Prophet
        candidates["prophet"] = _evaluate_prophet(train_ts, val_ts)
        
        # Select best model by validation MAE
        best_model_name = "linear"
        best_mae = float("inf")
        
        for name, val_metrics in candidates.items():
            if val_metrics and val_metrics["mae"] < best_mae:
                best_mae = val_metrics["mae"]
                best_model_name = name
                
        # ── 2. TRAIN BEST MODEL ON FULL DATA & FORECAST ────────────────────────
        historical_points = []
        for i in range(len(ts)):
            historical_points.append(
                ForecastPoint(
                    date=str(ts.index[i].date()),
                    value=round(float(ts.iloc[i]), 2),
                    lower_bound=round(float(ts.iloc[i]), 2),
                    upper_bound=round(float(ts.iloc[i]), 2),
                    is_forecast=False,
                )
            )

        # Scale future step count by the frequency
        if freq == "W":
            steps = max(1, horizon // 7)
        elif freq in ("ME", "M"):
            steps = max(1, horizon // 30)
        elif freq in ("QE", "Q"):
            steps = max(1, horizon // 90)
        elif freq in ("YE", "Y", "A"):
            steps = max(1, horizon // 365)
        else:
            steps = horizon

        forecast_points, final_metrics = _fit_and_predict(ts, best_model_name, steps, delta, val_ts)

        direction = "rising" if forecast_points[-1].value > ts.iloc[-1] else "falling" if forecast_points[-1].value < ts.iloc[-1] else "stable"
        
        # Business explanation
        pct_change = ((forecast_points[-1].value - ts.iloc[-1]) / abs(ts.iloc[-1]) * 100) if ts.iloc[-1] != 0 else 0
        direction_phrase = "increase by {:.1f}%".format(pct_change) if pct_change > 0 else "decrease by {:.1f}%".format(abs(pct_change)) if pct_change < 0 else "remain stable"
        
        interpretation = (
            f"Model selection engine identified '{best_model_name.upper()}' as the highest-accuracy model "
            f"(Validation R²={final_metrics['r_squared']:.2f}, MAPE={final_metrics['mape']:.1f}%). "
            f"Metric '{col_name}' is projected to {direction_phrase} over the next {horizon} days."
        )

        return ForecastResult(
            column=col_name,
            model_used=best_model_name,
            horizon_days=horizon,
            historical=historical_points[-60:],
            forecast=forecast_points,
            metrics=final_metrics,
            interpretation=interpretation,
            trend_direction=direction,
            confidence_level=min(max(final_metrics["r_squared"] * 100, 50), 95)
        )
    except Exception as e:
        logger.warning(f"Forecasting pipeline failed for {col_name}: {e}", exc_info=True)
        return None


# ── EVALUATION HELPERS ────────────────────────────────────────────────────────

def _evaluate_linear(train_ts: pd.Series, val_ts: pd.Series) -> Optional[Dict[str, float]]:
    try:
        x_train = np.arange(len(train_ts))
        slope, intercept, r_val, _, _ = stats.linregress(x_train, train_ts.values)
        
        x_val = np.arange(len(train_ts), len(train_ts) + len(val_ts))
        preds = slope * x_val + intercept
        
        return _calculate_val_metrics(val_ts.values, preds)
    except Exception:
        return None


def _evaluate_xgboost(train_ts: pd.Series, val_ts: pd.Series) -> Optional[Dict[str, float]]:
    try:
        import xgboost as xgb
        
        X_train, y_train = _build_lag_features(train_ts.values)
        if len(X_train) < 3:
            return None
            
        model = xgb.XGBRegressor(n_estimators=30, max_depth=3, random_state=42)
        model.fit(X_train, y_train)
        
        # Predict validation recursively
        preds = []
        current_lags = list(train_ts.values[-3:])
        for i in range(len(val_ts)):
            idx_feature = len(train_ts) + i
            features = np.array([[idx_feature] + current_lags])
            pred_val = float(model.predict(features)[0])
            preds.append(pred_val)
            # update lags
            current_lags.pop(0)
            current_lags.append(pred_val)
            
        return _calculate_val_metrics(val_ts.values, np.array(preds))
    except Exception:
        return None


def _evaluate_random_forest(train_ts: pd.Series, val_ts: pd.Series) -> Optional[Dict[str, float]]:
    try:
        from sklearn.ensemble import RandomForestRegressor
        
        X_train, y_train = _build_lag_features(train_ts.values)
        if len(X_train) < 3:
            return None
            
        model = RandomForestRegressor(n_estimators=30, max_depth=3, random_state=42)
        model.fit(X_train, y_train)
        
        # Predict validation recursively
        preds = []
        current_lags = list(train_ts.values[-3:])
        for i in range(len(val_ts)):
            idx_feature = len(train_ts) + i
            features = np.array([[idx_feature] + current_lags])
            pred_val = float(model.predict(features)[0])
            preds.append(pred_val)
            # update lags
            current_lags.pop(0)
            current_lags.append(pred_val)
            
        return _calculate_val_metrics(val_ts.values, np.array(preds))
    except Exception:
        return None


def _evaluate_exponential_smoothing(train_ts: pd.Series, val_ts: pd.Series) -> Optional[Dict[str, float]]:
    try:
        from statsmodels.tsa.holtwinters import ExponentialSmoothing
        model = ExponentialSmoothing(train_ts.values, trend="add", seasonal=None)
        fit = model.fit()
        preds = fit.forecast(len(val_ts))
        return _calculate_val_metrics(val_ts.values, preds)
    except Exception:
        return None


def _evaluate_prophet(train_ts: pd.Series, val_ts: pd.Series) -> Optional[Dict[str, float]]:
    try:
        from prophet import Prophet
        
        df_train = pd.DataFrame({"ds": train_ts.index, "y": train_ts.values})
        model = Prophet(yearly_seasonality=False, weekly_seasonality=False, daily_seasonality=False)
        model.fit(df_train)
        
        future = pd.DataFrame({"ds": val_ts.index})
        forecast = model.predict(future)
        return _calculate_val_metrics(val_ts.values, forecast["yhat"].values)
    except Exception:
        return None


def _calculate_val_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    mae = float(np.mean(np.abs(y_true - y_pred)))
    rmse = float(np.sqrt(np.mean((y_true - y_pred)**2)))
    
    # MAPE
    denom = np.where(y_true == 0, 1e-5, y_true)
    mape = float(np.mean(np.abs((y_true - y_pred) / denom)) * 100)
    
    # R2
    ss_res = np.sum((y_true - y_pred)**2)
    ss_tot = np.sum((y_true - np.mean(y_true))**2)
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    
    return {
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "mape": round(mape, 2),
        "r_squared": round(r2, 4)
    }


def _build_lag_features(values: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Create lags 1, 2, 3 feature matrix."""
    X, y = [], []
    for i in range(3, len(values)):
        X.append([i, values[i-1], values[i-2], values[i-3]])
        y.append(values[i])
    return np.array(X), np.array(y)


# ── FITTING AND FORECASTING HELPERS ──────────────────────────────────────────

def _fit_and_predict(
    ts: pd.Series,
    model_name: str,
    steps: int,
    delta: Any,
    val_ts: pd.Series
) -> Tuple[List[ForecastPoint], Dict[str, float]]:
    """Fit selected model on full series and predict steps ahead."""
    
    freq = ts.index.freqstr
    vals = ts.values
    last_date = ts.index[-1]
    
    future_preds = []
    std_err = float(np.std(vals))
    
    if model_name == "xgboost":
        try:
            import xgboost as xgb
            X_all, y_all = _build_lag_features(vals)
            model = xgb.XGBRegressor(n_estimators=50, max_depth=4, random_state=42)
            model.fit(X_all, y_all)
            
            # Predict recursively
            current_lags = list(vals[-3:])
            for d in range(1, steps + 1):
                idx_feature = len(vals) + d
                features = np.array([[idx_feature] + current_lags])
                pred = float(model.predict(features)[0])
                future_preds.append(pred)
                current_lags.pop(0)
                current_lags.append(pred)
                
            fit_preds = model.predict(X_all)
            residuals = y_all - fit_preds
            std_err = float(np.std(residuals)) if len(residuals) > 1 else float(np.std(vals))
        except Exception:
            model_name = "linear"

    elif model_name == "random_forest":
        try:
            from sklearn.ensemble import RandomForestRegressor
            X_all, y_all = _build_lag_features(vals)
            model = RandomForestRegressor(n_estimators=50, max_depth=4, random_state=42)
            model.fit(X_all, y_all)
            
            # Predict recursively
            current_lags = list(vals[-3:])
            for d in range(1, steps + 1):
                idx_feature = len(vals) + d
                features = np.array([[idx_feature] + current_lags])
                pred = float(model.predict(features)[0])
                future_preds.append(pred)
                current_lags.pop(0)
                current_lags.append(pred)
                
            fit_preds = model.predict(X_all)
            residuals = y_all - fit_preds
            std_err = float(np.std(residuals)) if len(residuals) > 1 else float(np.std(vals))
        except Exception:
            model_name = "linear"

    elif model_name == "exponential_smoothing":
        try:
            from statsmodels.tsa.holtwinters import ExponentialSmoothing
            model = ExponentialSmoothing(vals, trend="add", seasonal=None)
            fit = model.fit()
            future_preds = list(fit.forecast(steps))
            
            residuals = vals - fit.fittedvalues
            std_err = float(np.std(residuals)) if len(residuals) > 1 else float(np.std(vals))
        except Exception:
            model_name = "linear"
            
    if model_name == "prophet":
        try:
            from prophet import Prophet
            df_all = pd.DataFrame({"ds": ts.index, "y": vals})
            model = Prophet(yearly_seasonality=False, weekly_seasonality=False, daily_seasonality=False)
            model.fit(df_all)
            
            future = model.make_future_dataframe(periods=steps, freq=freq)
            forecast = model.predict(future)
            
            # Future points
            forecast_points = []
            n_hist = len(ts)
            for i in range(n_hist, len(forecast)):
                row = forecast.iloc[i]
                forecast_points.append(
                    ForecastPoint(
                        date=str(row["ds"].date()),
                        value=round(float(row["yhat"]), 2),
                        lower_bound=round(float(row["yhat_lower"]), 2),
                        upper_bound=round(float(row["yhat_upper"]), 2),
                        is_forecast=True
                    )
                )
            
            val_preds = forecast.iloc[len(ts)-len(val_ts):len(ts)]["yhat"].values
            metrics = _calculate_val_metrics(val_ts.values, val_preds)
            return forecast_points, metrics
        except Exception:
            model_name = "linear"

    if model_name == "linear":
        x = np.arange(len(ts))
        slope, intercept, r_val, _, _ = stats.linregress(x, vals)
        
        for d in range(1, steps + 1):
            future_preds.append(slope * (len(ts) + d) + intercept)
            
        fit_preds = slope * x + intercept
        residuals = vals - fit_preds
        std_err = float(np.std(residuals)) if len(residuals) > 1 else float(np.std(vals))

    # Re-evaluate best model metrics on validation split
    if model_name == "linear":
        x_val = np.arange(len(ts) - len(val_ts), len(ts))
        val_preds = slope * x_val + intercept
        metrics = _calculate_val_metrics(val_ts.values, val_preds)
    elif model_name == "xgboost":
        val_eval = _evaluate_xgboost(ts.iloc[:-len(val_ts)], val_ts)
        metrics = val_eval if val_eval else _calculate_val_metrics(val_ts.values, vals[-len(val_ts):])
    elif model_name == "random_forest":
        val_eval = _evaluate_random_forest(ts.iloc[:-len(val_ts)], val_ts)
        metrics = val_eval if val_eval else _calculate_val_metrics(val_ts.values, vals[-len(val_ts):])
    elif model_name == "exponential_smoothing":
        val_eval = _evaluate_exponential_smoothing(ts.iloc[:-len(val_ts)], val_ts)
        metrics = val_eval if val_eval else _calculate_val_metrics(val_ts.values, vals[-len(val_ts):])
        
    forecast_points = []
    for d in range(1, steps + 1):
        pred_val = future_preds[d-1]
        ci = 1.96 * std_err * np.sqrt(d)
        forecast_date = last_date + d * delta
        forecast_points.append(
            ForecastPoint(
                date=str(forecast_date.date()),
                value=round(float(pred_val), 2),
                lower_bound=round(float(pred_val - ci), 2),
                upper_bound=round(float(pred_val + ci), 2),
                is_forecast=True
            )
        )
        
    return forecast_points, metrics


def detect_forecastable_columns(
    df: pd.DataFrame,
    date_col: str,
    numeric_cols: List[str],
) -> List[Dict[str, Any]]:
    """Identify which numeric columns are suitable for forecasting."""
    results = []
    try:
        dates = pd.to_datetime(df[date_col], errors="coerce")
    except Exception:
        return results

    for col in numeric_cols[:10]:
        if col not in df.columns:
            continue
        series = df[col].dropna()
        if len(series) < 10:
            continue

        ts = pd.DataFrame({"date": dates, "value": df[col]}).dropna()
        ts = ts.sort_values("date")
        ts_agg = ts.set_index("date").resample("D")["value"].mean().dropna()

        if len(ts_agg) < 5:
            continue

        cv = ts_agg.std() / ts_agg.mean() if ts_agg.mean() != 0 else 0
        results.append(
            {
                "column": col,
                "data_points": len(ts_agg),
                "date_range_days": (ts_agg.index[-1] - ts_agg.index[0]).days,
                "variation_coefficient": round(float(cv), 4),
                "forecastable": cv > 0.01,
            }
        )

    return [r for r in results if r["forecastable"]]
