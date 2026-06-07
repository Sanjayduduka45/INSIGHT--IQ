"""
InsightIQ — Smart Visualization Engine

Recommends and structures charts for dashboards.
Prioritizes key business metrics (revenue, profit, categories, regions)
and assigns a relevance score to each visualization.
"""

from __future__ import annotations

import logging
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional
from intelligence.schema_detector import DatasetSchema
from core.df_utils import get_analytic_numeric_cols, get_categorical_cols

logger = logging.getLogger(__name__)


def recommend_charts(df: pd.DataFrame, schema: DatasetSchema) -> List[Dict[str, Any]]:
    """Automatically generate chart recommendations sorted by business relevance score.

    Excludes ID-like and constant columns.
    """
    charts: List[Dict[str, Any]] = []
    num_cols = get_analytic_numeric_cols(df, schema)
    cat_cols = get_categorical_cols(df, schema)

    # Scanners for prioritization
    rev_keywords = ["revenue", "sales", "spend", "amount", "total", "price", "cost", "value"]
    profit_keywords = ["profit", "margin", "earnings", "net"]
    region_keywords = ["region", "state", "country", "city", "location"]

    primary_metric = num_cols[0] if num_cols else None

    # ── 1. TREND CHART ────────────────────────────────────────────────────
    if schema.date_columns and num_cols:
        date_col = schema.date_columns[0]
        for metric in num_cols[:2]:
            try:
                df_agg = df.groupby(date_col)[metric].sum().reset_index()
                df_agg = df_agg.sort_values(date_col).head(30)
                df_agg["rolling_mean"] = df_agg[metric].rolling(window=7, min_periods=1).mean()
                
                # Score trend relevance
                is_rev = any(kw in metric.lower() for kw in rev_keywords)
                is_prof = any(kw in metric.lower() for kw in profit_keywords)
                score = 98.0 if (is_rev or is_prof) else 80.0
                
                charts.append(
                    {
                        "type": "trend",
                        "title": f"{metric} Trend Over Time",
                        "x_axis": date_col,
                        "y_axis": metric,
                        "relevance_score": score,
                        "data": [
                            {
                                "date": str(row[date_col]),
                                "value": round(float(row[metric]), 2),
                                "moving_average": round(float(row["rolling_mean"]), 2),
                            }
                            for _, row in df_agg.iterrows()
                        ],
                    }
                )
            except Exception as e:
                logger.warning("Trend chart generation failed: %s", e)

    # ── 2. PARETO / CONTRIBUTION CHART ────────────────────────────────────
    if cat_cols and num_cols:
        for cat in cat_cols[:2]:
            for metric in num_cols[:2]:
                try:
                    df_grouped = df.groupby(cat)[metric].sum().reset_index()
                    df_grouped = df_grouped.sort_values(metric, ascending=False).head(10)
                    total = df_grouped[metric].sum()

                    cum_pct = 0.0
                    data = []
                    for _, row in df_grouped.iterrows():
                        val = float(row[metric])
                        cum_pct += (val / total * 100) if total != 0 else 0
                        data.append({"name": str(row[cat]), "value": val, "cumulative": round(cum_pct, 1)})
                    
                    # Score Pareto relevance
                    is_rev = any(kw in metric.lower() for kw in rev_keywords)
                    is_region = any(kw in cat.lower() for kw in region_keywords)
                    score = 92.0 if is_rev else 85.0
                    if is_region:
                        score += 3.0
                        
                    charts.append(
                        {
                            "type": "pareto",
                            "title": f"Pareto Analysis: {cat} by {metric}",
                            "x_axis": cat,
                            "y_axis": metric,
                            "relevance_score": score,
                            "data": data,
                        }
                    )
                except Exception as e:
                    logger.warning("Pareto chart generation failed: %s", e)

    # ── 3. CORRELATION HEATMAP ─────────────────────────────────────────────
    if len(num_cols) >= 3:
        try:
            cols = num_cols[:6]
            corr = df[cols].corr().round(2).fillna(0)
            data = []
            for col1 in cols:
                for col2 in cols:
                    data.append({"x": col1, "y": col2, "value": float(corr.loc[col1, col2])})
            charts.append(
                {
                    "type": "heatmap",
                    "title": "Metric Interaction Heatmap",
                    "relevance_score": 88.0,
                    "data": data,
                    "columns": cols,
                }
            )
        except Exception as e:
            logger.warning("Heatmap generation failed: %s", e)

    # ── 4. TREEMAP (Category Distribution) ────────────────────────────────
    if cat_cols and num_cols:
        cat = cat_cols[0]
        metric = num_cols[0]
        try:
            df_grouped = df.groupby(cat)[metric].sum().reset_index()
            df_grouped = df_grouped.sort_values(metric, ascending=False).head(8)
            charts.append(
                {
                    "type": "treemap",
                    "title": f"Volume Concentration: {metric} Share by {cat}",
                    "relevance_score": 85.0,
                    "data": [
                        {"name": str(row[cat]), "size": float(row[metric])}
                        for _, row in df_grouped.iterrows()
                    ],
                }
            )
        except Exception as e:
            logger.warning("Treemap generation failed: %s", e)

    # ── 5. SCATTER PLOT (Relationships) ───────────────────────────────────
    if len(num_cols) >= 2:
        try:
            cols = num_cols[:6]
            corr = df[cols].corr().abs().fillna(0)
            max_val = -1.0
            best_pair = (cols[0], cols[1])
            for i in range(len(cols)):
                for j in range(i + 1, len(cols)):
                    val = float(corr.iloc[i, j])
                    if val > max_val and val < 0.99:
                        max_val = val
                        best_pair = (cols[i], cols[j])

            c1, c2 = best_pair
            sample_df = df[[c1, c2]].dropna().head(100)
            charts.append(
                {
                    "type": "scatter",
                    "title": f"Bivariate Distribution: {c1} vs {c2}",
                    "x_axis": c1,
                    "y_axis": c2,
                    "relevance_score": 80.0,
                    "data": [
                        {"x": float(row[c1]), "y": float(row[c2])}
                        for _, row in sample_df.iterrows()
                    ],
                }
            )
        except Exception as e:
            logger.warning("Scatter plot generation failed: %s", e)

    # ── 6. BOXPLOT (Distribution spreads) ─────────────────────────────────
    if cat_cols and num_cols:
        cat = cat_cols[0]
        metric = num_cols[0]
        try:
            top_cats = df[cat].value_counts().head(5).index
            data = []
            for c in top_cats:
                sub = df[df[cat] == c][metric].dropna()
                if len(sub) >= 5:
                    data.append(
                        {
                            "name": str(c),
                            "min": float(sub.min()),
                            "q1": float(sub.quantile(0.25)),
                            "median": float(sub.quantile(0.50)),
                            "q3": float(sub.quantile(0.75)),
                            "max": float(sub.max()),
                        }
                    )
            if data:
                charts.append(
                    {
                        "type": "boxplot",
                        "title": f"{metric} Variance across {cat} Categories",
                        "x_axis": cat,
                        "y_axis": metric,
                        "relevance_score": 78.0,
                        "data": data,
                    }
                )
        except Exception as e:
            logger.warning("Boxplot generation failed: %s", e)

    # ── 7. PIE CHART ──────────────────────────────────────────────────────
    if cat_cols:
        cat = cat_cols[0]
        try:
            vc = df[cat].dropna().astype(str).value_counts().head(8)
            total = vc.sum()
            if not vc.empty and total > 0:
                charts.append(
                    {
                        "type": "pie",
                        "title": f"{cat} Composition Share",
                        "relevance_score": 70.0,
                        "data": [
                            {
                                "name": str(k),
                                "value": int(v),
                                "pct": round(int(v) / total * 100, 1),
                            }
                            for k, v in vc.items()
                        ],
                    }
                )
        except Exception as e:
            logger.warning("Pie chart generation failed: %s", e)

    # ── 8. HISTOGRAM (Spread spreads) ─────────────────────────────────────
    if num_cols:
        metric = num_cols[0]
        try:
            series = df[metric].dropna()
            if not series.empty:
                counts, edges = np.histogram(series, bins=10)
                data = []
                for i in range(len(counts)):
                    bin_label = f"{edges[i]:.1f}-{edges[i+1]:.1f}"
                    data.append({"bin": bin_label, "count": int(counts[i])})
                charts.append(
                    {
                        "type": "histogram",
                        "title": f"Distribution Frequency: {metric}",
                        "x_axis": "Value Bin",
                        "y_axis": "Frequency",
                        "relevance_score": 65.0,
                        "data": data,
                    }
                )
        except Exception as e:
            logger.warning("Histogram generation failed: %s", e)

    # Sort recommendations by relevance score descending
    charts.sort(key=lambda c: c.get("relevance_score", 0.0), reverse=True)
    return charts
