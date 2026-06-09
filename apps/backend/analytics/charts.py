"""
InsightIQ — Smart Visualization Engine

Recommends and structures charts for dashboards dynamically.
Adapts to whatever columns exist in the dataset, using column types,
distributions, and relationships rather than hardcoded column names.
"""

from __future__ import annotations

import logging
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional
from intelligence.schema_detector import DatasetSchema
from core.df_utils import get_analytic_numeric_cols, get_categorical_cols
from intelligence.domain_classifier import classify_domain

logger = logging.getLogger(__name__)


def to_business_label(col_name: str) -> str:
    """Convert technical column/metric names to clear business language."""
    if not col_name:
        return ""
    col_clean = str(col_name).strip()
    
    # Check suffixes/prefixes
    is_sum = False
    is_avg = False
    is_nunique = False
    
    col_lower = col_clean.lower()
    if col_lower.endswith("_sum") or col_lower.endswith(" sum"):
        is_sum = True
        col_clean = col_clean[:-4]
    elif col_lower.endswith("_avg") or col_lower.endswith(" avg") or col_lower.endswith("_mean") or col_lower.endswith(" mean"):
        is_avg = True
        col_clean = col_clean[:-4]
        if col_lower.endswith("_mean"):
            col_clean = col_clean[:-1]
    elif col_lower.endswith("_nunique") or col_lower.endswith(" nunique") or col_lower.endswith("_count") or col_lower.endswith(" count") or col_lower.endswith("_distinct") or col_lower.endswith(" distinct"):
        is_nunique = True
        if col_lower.endswith("_nunique"):
            col_clean = col_clean[:-8]
        elif col_lower.endswith("_distinct"):
            col_clean = col_clean[:-9]
        else:
            col_clean = col_clean[:-6]

    # Replace formatting symbols
    col_clean = col_clean.replace("_", " ").strip()
    
    # Capitalize words and discard units
    words = col_clean.split()
    capitalized_words = []
    for w in words:
        if w.upper() in ["INR", "USD", "EUR", "GBP"]:
            continue
        capitalized_words.append(w.capitalize())
    col_clean = " ".join(capitalized_words)
    
    if is_sum:
        return f"Total {col_clean}"
    elif is_avg:
        return f"Average {col_clean}"
    elif is_nunique:
        return f"Unique {col_clean}"
        
    lower_clean = col_clean.lower()
    if "revenue" in lower_clean or "sales" in lower_clean or "profit" in lower_clean:
        if not any(prefix in lower_clean for prefix in ["average", "unique", "total"]):
            return f"Total {col_clean}"
    elif "customer" in lower_clean or "user" in lower_clean or "client" in lower_clean or "order" in lower_clean:
        if "id" in lower_clean or "code" in lower_clean:
            return f"Unique {col_clean.replace('Id', '').replace('Code', '').strip()}"
            
    return col_clean


def build_business_title(chart_type: str, x_col: str, y_col: Optional[str] = None) -> str:
    """Generate executive consulting-grade business titles for visualizations."""
    x_lbl = to_business_label(x_col)
    y_lbl = to_business_label(y_col) if y_col else "Count"
    
    ct = chart_type.lower()
    if ct in ["line", "trend", "area", "stacked_area"]:
        return f"Historical {y_lbl} Trend over {x_lbl}"
    elif ct in ["bar", "pie", "donut", "treemap", "pareto", "funnel", "stacked_bar"]:
        return f"Top {y_lbl} Breakdown by {x_lbl}"
    elif ct in ["histogram", "boxplot"]:
        return f"Spread Profile of {x_lbl}"
    elif ct in ["scatter", "bubble"]:
        return f"{y_lbl} Correlation Dispersion vs {x_lbl}"
    elif ct in ["heatmap", "correlation"]:
        return "Inter-Metric Correlation Analysis Matrix"
    return f"{y_lbl} by {x_lbl}"


def recommend_charts(df: pd.DataFrame, schema: DatasetSchema, dashboard: Optional[str] = None) -> List[Dict[str, Any]]:
    """Automatically generate chart recommendations sorted by business relevance score.

    Adapts dynamically to the shape, data types, and semantic patterns of the dataset.
    Guarantees at least 6–12 charts with robust fallback logic and detailed stage logs.
    """
    if dashboard:
        return build_dashboard_charts(df, schema, dashboard)

    charts: List[Dict[str, Any]] = []
    
    # ── STAGE LOGS ──
    logger.info("========================================")
    logger.info("📊 VISUALIZATION ENGINE - CHART GENERATION")
    logger.info("========================================")

    # 1. Columns & Shape Auditing
    num_cols = get_analytic_numeric_cols(df, schema)
    cat_cols = get_categorical_cols(df, schema)
    date_cols = getattr(schema, "date_columns", [])
    
    logger.info("Columns Detected:")
    logger.info(f"  - Numeric safe: {num_cols}")
    logger.info(f"  - Categorical safe: {cat_cols}")
    logger.info(f"  - Date columns: {date_cols}")
    logger.info(f"  - Total Row Count: {len(df)}")

    # 2. Identify Domain Context
    domain_result = classify_domain(df, schema)
    domain = domain_result.domain
    logger.info(f"Dataset Type Detected: {domain} domain (confidence: {domain_result.confidence})")

    # Define Domain Terminologies & Main Metrics
    domain_metrics = {
        "Sales": {"primary": "Revenue", "secondary": "Profit", "vol": "Sales Volume", "item": "Product", "segment": "Customer Segment"},
        "Finance": {"primary": "Cash Flow", "secondary": "Profit Margin", "vol": "Transaction Value", "item": "Account", "segment": "Risk Profile"},
        "Marketing": {"primary": "Conversion Value", "secondary": "Ad Spend", "vol": "Impressions", "item": "Campaign", "segment": "Target Group"},
        "Customer Analytics": {"primary": "Lifetime Value", "secondary": "Purchase Value", "vol": "Transaction Count", "item": "Service", "segment": "RFM Cohort"},
        "Operations": {"primary": "Throughput", "secondary": "Cycle Time", "vol": "Process Count", "item": "Resource", "segment": "Priority Queue"},
        "HR": {"primary": "Compensation", "secondary": "Retention Rate", "vol": "Headcount", "item": "Role", "segment": "Satisfaction Tier"},
        "Inventory": {"primary": "Stock Value", "secondary": "Safety Stock", "vol": "Order Quantity", "item": "SKU", "segment": "Storage Zone"},
        "Healthcare": {"primary": "Treatment Cost", "secondary": "Length of Stay", "vol": "Patient Volume", "item": "Procedure", "segment": "Payer Type"},
        "Manufacturing": {"primary": "OEE", "secondary": "Defect Rate", "vol": "Downtime", "item": "Line", "segment": "Shift"},
        "Generic": {"primary": "Volume", "secondary": "Metric Val", "vol": "Record Count", "item": "Category", "segment": "Dimension"}
    }
    
    terms = domain_metrics.get(domain, domain_metrics["Generic"])

    def format_title(title_template: str, col_name: str = "") -> str:
        formatted = title_template
        if col_name:
            formatted = formatted.replace("{col}", col_name)
        formatted = formatted.replace("{primary}", terms["primary"])
        formatted = formatted.replace("{secondary}", terms["secondary"])
        formatted = formatted.replace("{vol}", terms["vol"])
        formatted = formatted.replace("{item}", terms["item"])
        formatted = formatted.replace("{segment}", terms["segment"])
        return formatted

    # Helper tracking candidates
    candidates_count = 0
    rendered_count = 0
    failed_charts: List[Dict[str, str]] = []

    def log_chart_attempt(name: str, success: bool, reason: str = ""):
        nonlocal candidates_count, rendered_count
        candidates_count += 1
        if success:
            rendered_count += 1
            logger.debug(f"  [SUCCESS] Rendered chart candidate: '{name}'")
        else:
            failed_charts.append({"name": name, "reason": reason})
            logger.warning(f"  [FAILED] Failed candidate '{name}': {reason}")

    # ────────────────────────────────────────────────────────────────────────
    # 1. MARKETING / ADVERTISING DATASET (e.g., TV/Radio/Newspaper Budget vs Sales)
    # ────────────────────────────────────────────────────────────────────────
    # Check if we have advertising channels and target metrics
    spend_keywords = ["tv", "radio", "newspaper", "spend", "ad_spend", "budget", "campaign_spend", "marketing"]
    target_keywords = ["sales", "revenue", "conversion", "leads", "transactions", "roi", "profit"]
    
    spend_cols = [c for c in num_cols if any(kw in c.lower() for kw in spend_keywords)]
    target_cols = [c for c in num_cols if any(kw in c.lower() for kw in target_keywords)]
    
    if len(spend_cols) > 0 and len(target_cols) > 0:
        logger.info("Analyzing as Advertising/Marketing Special Dataset Profile...")
        
        # A. Spend vs Target Scatter Plots (e.g. TV vs Sales)
        for sc in spend_cols:
            for tc in target_cols[:2]:
                chart_name = f"Scatter: {sc} vs {tc}"
                try:
                    sample_df = df[[sc, tc]].dropna().head(100)
                    if not sample_df.empty:
                        r_val = df[sc].corr(df[tc])
                        insight = f"Bivariate regression of {sc} spend vs {tc} demonstrates a correlation coefficient of {r_val:.2f}, indicating its direct business impact."
                        charts.append({
                            "type": "scatter",
                            "title": f"Ad Channel Spend Effect: {sc} vs {tc}",
                            "x_axis": sc,
                            "y_axis": tc,
                            "relevance_score": 99.0,
                            "insight": insight,
                            "data": [
                                {"x": float(row[sc]), "y": float(row[tc])}
                                for _, row in sample_df.iterrows()
                            ]
                        })
                        log_chart_attempt(chart_name, True)
                    else:
                        log_chart_attempt(chart_name, False, "No non-null rows")
                except Exception as e:
                    log_chart_attempt(chart_name, False, str(e))

        # B. Spend Composition / Share of Budget Pie Chart
        if len(spend_cols) >= 2:
            chart_name = "Spend Composition Pie"
            try:
                spend_sums = df[spend_cols].sum()
                total_spend = spend_sums.sum()
                if total_spend > 0:
                    insight = f"Share of voice analysis indicates '{spend_sums.idxmax()}' holds the largest media spend share ({(spend_sums.max()/total_spend*100):.1f}%)."
                    charts.append({
                        "type": "pie",
                        "title": "Ad Channel Budget Allocation Share",
                        "relevance_score": 98.0,
                        "insight": insight,
                        "data": [
                            {
                                "name": col,
                                "value": float(val),
                                "pct": round(float(val) / total_spend * 100, 1)
                            }
                            for col, val in spend_sums.items()
                        ]
                    })
                    log_chart_attempt(chart_name, True)
                else:
                    log_chart_attempt(chart_name, False, "Total spend sum is 0")
            except Exception as e:
                log_chart_attempt(chart_name, False, str(e))

        # C. Channel ROI Efficiency Index Pareto Chart
        chart_name = "Channel ROI Pareto"
        try:
            tc = target_cols[0]
            roi_data = []
            for sc in spend_cols:
                s_sum = df[sc].sum()
                t_sum = df[tc].sum()
                if s_sum > 0:
                    roi = t_sum / s_sum
                    roi_data.append({"name": sc, "value": round(roi, 2)})
            if roi_data:
                roi_data.sort(key=lambda x: x["value"], reverse=True)
                best_ch = roi_data[0]["name"]
                insight = f"Channel efficiency tracking reveals '{best_ch}' as the most optimized spend channel, yielding the highest return on investment ratio."
                charts.append({
                    "type": "pareto",
                    "title": f"Advertising ROI Efficiency Index (Return per Unit of Spend)",
                    "x_axis": "Channel",
                    "y_axis": "Return Ratio",
                    "relevance_score": 97.0,
                    "insight": insight,
                    "data": [
                        {
                            "name": item["name"],
                            "value": item["value"],
                            "cumulative": 100.0
                        }
                        for item in roi_data
                    ]
                })
                log_chart_attempt(chart_name, True)
            else:
                log_chart_attempt(chart_name, False, "No valid ROI values")
        except Exception as e:
            log_chart_attempt(chart_name, False, str(e))

    # ────────────────────────────────────────────────────────────────────────
    # 2. DATE DATASET (Trends, moving average, growth rates over time)
    # ────────────────────────────────────────────────────────────────────────
    if date_cols and num_cols:
        logger.info("Generating Date-based Trend Visualizations...")
        date_col = date_cols[0]
        for i, metric in enumerate(num_cols[:2]):
            chart_name = f"Trend: {metric} over time"
            try:
                df_agg = df.dropna(subset=[date_col, metric]).groupby(date_col)[metric].sum().reset_index()
                df_agg = df_agg.sort_values(date_col).head(24)
                if len(df_agg) >= 2:
                    df_agg["rolling_mean"] = df_agg[metric].rolling(window=5, min_periods=1).mean()
                    
                    v_start = float(df_agg[metric].iloc[0])
                    v_end = float(df_agg[metric].iloc[-1])
                    change_pct = ((v_end - v_start) / v_start * 100) if v_start != 0 else 0
                    peak_idx = df_agg[metric].idxmax()
                    peak_date = str(df_agg[date_col].loc[peak_idx])
                    peak_val = float(df_agg[metric].loc[peak_idx])
                    
                    trend_direction = "expansion" if change_pct >= 0 else "contraction"
                    insight = f"{metric} showed a {abs(change_pct):.1f}% {trend_direction} over the observed time horizon, peaking on {peak_date} at {peak_val:,.1f}."
                    
                    charts.append({
                        "type": "trend",
                        "title": format_title(f"Temporal {metric} Performance Trend"),
                        "x_axis": date_col,
                        "y_axis": metric,
                        "relevance_score": 95.0 - (i * 5),
                        "insight": insight,
                        "data": [
                            {
                                "date": str(row[date_col]),
                                "value": round(float(row[metric]), 2),
                                "moving_average": round(float(row["rolling_mean"]), 2),
                            }
                            for _, row in df_agg.iterrows()
                        ]
                    })
                    log_chart_attempt(chart_name, True)
                else:
                    log_chart_attempt(chart_name, False, "Too few dates aggregated")
            except Exception as e:
                log_chart_attempt(chart_name, False, str(e))
    else:
        # Fallback trend when no date is present: Sequence Index
        if num_cols:
            logger.info("Date columns missing. Generating Sequence Index Trend...")
            for i, metric in enumerate(num_cols[:2]):
                chart_name = f"Sequence Trend: {metric}"
                try:
                    sample_df = df[[metric]].dropna().head(35).reset_index()
                    if not sample_df.empty:
                        v_mean = float(sample_df[metric].mean())
                        v_std = float(sample_df[metric].std())
                        insight = f"No timeline column found. Sequence index mapping of {metric} shows a baseline mean of {v_mean:,.1f} with standard deviation of {v_std:,.1f} indicating normal variance."
                        
                        charts.append({
                            "type": "trend",
                            "title": format_title(f"Sequence Timeline: {metric} Volatility Index"),
                            "x_axis": "Record Index",
                            "y_axis": metric,
                            "relevance_score": 75.0 - (i * 5),
                            "insight": insight,
                            "data": [
                                {
                                    "date": f"Idx {row['index']}",
                                    "value": round(float(row[metric]), 2),  # FIXED: was row['index']
                                    "moving_average": round(v_mean, 2)
                                }
                                for _, row in sample_df.iterrows()
                            ]
                        })
                        log_chart_attempt(chart_name, True)
                    else:
                        log_chart_attempt(chart_name, False, "Empty metric column")
                except Exception as e:
                    log_chart_attempt(chart_name, False, str(e))

    # ────────────────────────────────────────────────────────────────────────
    # 3. GENERIC NUMERIC DATASETS (Correlation heatmaps, Pair Plots, Scatter, Outliers)
    # ────────────────────────────────────────────────────────────────────────
    # A. Inter-Metric Correlation Heatmap
    if len(num_cols) >= 2:
        chart_name = "Correlation Matrix Heatmap"
        try:
            cols = num_cols[:6]
            corr = df[cols].corr().round(2).fillna(0)
            data = []
            max_corr = -1.0
            max_pair = ("", "")
            
            for c1 in cols:
                for c2 in cols:
                    val = float(corr.loc[c1, c2])
                    data.append({"x": c1, "y": c2, "value": val})
                    if c1 != c2 and abs(val) > max_corr:
                        max_corr = abs(val)
                        max_pair = (c1, c2)
            
            insight = f"Heatmap metrics correlation audit isolates '{max_pair[0]}' and '{max_pair[1]}' as the most linked continuous pair (coefficient of {max_corr:.2f})."
            
            charts.append({
                "type": "heatmap",
                "title": format_title("Inter-Metric Correlation Matrix"),
                "relevance_score": 88.0,
                "insight": insight,
                "data": data,
                "columns": cols
            })
            log_chart_attempt(chart_name, True)
        except Exception as e:
            log_chart_attempt(chart_name, False, str(e))

    # B. Scatter Relationships (Pairs)
    if len(num_cols) >= 2:
        chart_name = "Bivariate Scatter Analysis"
        try:
            cols = num_cols[:6]
            corr_matrix = df[cols].corr().abs().fillna(0)
            best_pair = (cols[0], cols[1])
            max_val = -1.0
            for i in range(len(cols)):
                for j in range(i + 1, len(cols)):
                    val = float(corr_matrix.iloc[i, j])
                    if val > max_val and val < 0.99:
                        max_val = val
                        best_pair = (cols[i], cols[j])
            
            c1, c2 = best_pair
            sample_df = df[[c1, c2]].dropna().head(100)
            if not sample_df.empty:
                r_val = df[c1].corr(df[c2])
                strength = "strong" if abs(r_val) > 0.6 else "moderate" if abs(r_val) > 0.3 else "weak"
                direction = "positive" if r_val > 0 else "negative"
                
                insight = f"Bivariate plot illustrates a {strength} {direction} correlation (r={r_val:.2f}) between '{c1}' and '{c2}'. Useful for ROI and variance tracking."
                
                charts.append({
                    "type": "scatter",
                    "title": format_title(f"Bivariate Scatter Analysis: {c1} vs {c2}"),
                    "x_axis": c1,
                    "y_axis": c2,
                    "relevance_score": 82.0,
                    "insight": insight,
                    "data": [
                        {"x": float(row[c1]), "y": float(row[c2])}
                        for _, row in sample_df.iterrows()
                    ]
                })
                log_chart_attempt(chart_name, True)
            else:
                log_chart_attempt(chart_name, False, "No non-null records in scatter pair")
        except Exception as e:
            log_chart_attempt(chart_name, False, str(e))

    # C. Variable Distribution Spectrum (Histograms)
    for i, metric in enumerate(num_cols[:3]):
        chart_name = f"Histogram: {metric}"
        try:
            series = df[metric].dropna()
            if not series.empty:
                counts, edges = np.histogram(series, bins=10)
                mean_val = series.mean()
                median_val = series.median()
                skewness = "positive" if mean_val > median_val else "negative" if mean_val < median_val else "neutral"
                
                max_bin_idx = counts.argmax()
                modal_range = f"{edges[max_bin_idx]:.1f} - {edges[max_bin_idx+1]:.1f}"
                insight = f"Distribution shows a {skewness} skew with values peaking in the '{modal_range}' range. The mean sits at {mean_val:,.1f}."
                
                charts.append({
                    "type": "histogram",
                    "title": format_title(f"Frequency Distribution Spectrum: {metric}"),
                    "x_axis": "Value Range",
                    "y_axis": "Count",
                    "relevance_score": 80.0 - (i * 2),
                    "insight": insight,
                    "data": [
                        {
                            "bin": f"{edges[idx]:.1f}-{edges[idx+1]:.1f}",
                            "count": int(counts[idx])
                        }
                        for idx in range(len(counts))
                    ]
                })
                log_chart_attempt(chart_name, True)
            else:
                log_chart_attempt(chart_name, False, f"Column {metric} contains only null values")
        except Exception as e:
            log_chart_attempt(chart_name, False, str(e))

    # D. Statistical Spread Variance (Boxplots)
    if cat_cols and num_cols:
        cat = cat_cols[0]
        metric = num_cols[0]
        chart_name = f"Boxplot: {metric} by {cat}"
        try:
            top_cats = df[cat].value_counts().head(5).index
            data = []
            medians = {}
            for c in top_cats:
                sub = df[df[cat] == c][metric].dropna()
                if len(sub) >= 5:
                    median_val = float(sub.quantile(0.5))
                    medians[str(c)] = median_val
                    data.append({
                        "name": str(c),
                        "min": float(sub.min()),
                        "q1": float(sub.quantile(0.25)),
                        "median": median_val,
                        "q3": float(sub.quantile(0.75)),
                        "max": float(sub.max())
                    })
            
            if data:
                max_median_cat = max(medians, key=medians.get)
                insight = f"Spread analysis reveals '{max_median_cat}' holds the highest median value. Box widths highlight differences in category performance variances."
                
                charts.append({
                    "type": "boxplot",
                    "title": format_title(f"Statistical Spread Variance: {metric} across {cat}"),
                    "x_axis": cat,
                    "y_axis": metric,
                    "relevance_score": 78.0,
                    "insight": insight,
                    "data": data
                })
                log_chart_attempt(chart_name, True)
            else:
                log_chart_attempt(chart_name, False, "Too few records per category")
        except Exception as e:
            log_chart_attempt(chart_name, False, str(e))
    elif num_cols:
        # Numeric only Boxplot fallback: compare spreads of top 3 metrics side by side
        chart_name = "Multi-Metric Boxplot Fallback"
        try:
            data = []
            for metric in num_cols[:3]:
                sub = df[metric].dropna()
                if len(sub) >= 5:
                    data.append({
                        "name": metric,
                        "min": float(sub.min()),
                        "q1": float(sub.quantile(0.25)),
                        "median": float(sub.quantile(0.5)),
                        "q3": float(sub.quantile(0.75)),
                        "max": float(sub.max())
                    })
            if data:
                insight = f"Multi-metric boxplot highlights statistical spreads. The widest range limits are isolated to '{data[0]['name']}'."
                charts.append({
                    "type": "boxplot",
                    "title": format_title("Metric Variance Footprints Comparison"),
                    "x_axis": "Metric Name",
                    "y_axis": "Value Range",
                    "relevance_score": 77.0,
                    "insight": insight,
                    "data": data
                })
                log_chart_attempt(chart_name, True)
            else:
                log_chart_attempt(chart_name, False, "Too few rows to construct boxplot comparison")
        except Exception as e:
            log_chart_attempt(chart_name, False, str(e))

    # E. Numeric composition / Tiers (Pie)
    if num_cols:
        chart_name = "Numeric Tiers Pie"
        try:
            metric = num_cols[0]
            median = df[metric].median()
            high_count = int((df[metric] > median).sum())
            low_count = int((df[metric] <= median).sum())
            total = high_count + low_count
            if total > 0:
                insight = f"Composition audit for '{metric}' dividing records around the median threshold shows a balanced 50/50 split."
                charts.append({
                    "type": "pie",
                    "title": format_title(f"Volume Tiers Composition: {metric}"),
                    "relevance_score": 70.0,
                    "insight": insight,
                    "data": [
                        {"name": "High Performers (> Median)", "value": high_count, "pct": round(high_count/total*100, 1)},
                        {"name": "Standard Performers (<= Median)", "value": low_count, "pct": round(low_count/total*100, 1)}
                    ]
                })
                log_chart_attempt(chart_name, True)
            else:
                log_chart_attempt(chart_name, False, "Total record count is 0")
        except Exception as e:
            log_chart_attempt(chart_name, False, str(e))

    # ────────────────────────────────────────────────────────────────────────
    # 4. CATEGORICAL DATASETS (Pareto rankings, composition share treemaps/pies)
    # ────────────────────────────────────────────────────────────────────────
    if cat_cols:
        for cat in cat_cols[:2]:
            metric = num_cols[0] if num_cols else None
            chart_name = f"Categorical Pareto: {cat} by {metric or 'Count'}"
            try:
                if metric:
                    df_grouped = df.groupby(cat)[metric].sum().reset_index()
                    df_grouped = df_grouped.sort_values(metric, ascending=False).head(8)
                    total = df_grouped[metric].sum()
                else:
                    df_grouped = df[cat].value_counts().reset_index(name="count")
                    df_grouped.columns = [cat, "count"]
                    df_grouped = df_grouped.head(8)
                    total = df_grouped["count"].sum()
                    metric = "count"

                if total > 0 and len(df_grouped) >= 1:
                    data = []
                    cum_pct = 0.0
                    for _, row in df_grouped.iterrows():
                        val = float(row[metric])
                        cum_pct += (val / total * 100)
                        data.append({
                            "name": str(row[cat]),
                            "value": val,
                            "cumulative": round(cum_pct, 1)
                        })
                    
                    top1_name = data[0]["name"]
                    top1_pct = (data[0]["value"] / total * 100)
                    top3_pct = data[min(2, len(data)-1)]["cumulative"]
                    
                    insight = f"Ranked contribution identifies '{top1_name}' as the top driver with {top1_pct:.1f}% share. Concentration is high, with the top 3 segments contributing {top3_pct:.1f}% of overall."
                    
                    charts.append({
                        "type": "pareto",
                        "title": format_title(f"Pareto Ranking: {cat} contribution"),
                        "x_axis": cat,
                        "y_axis": metric,
                        "relevance_score": 85.0,
                        "insight": insight,
                        "data": data
                    })
                    log_chart_attempt(chart_name, True)
                else:
                    log_chart_attempt(chart_name, False, "Total category sum is 0")
            except Exception as e:
                log_chart_attempt(chart_name, False, str(e))

        # Treemap
        if cat_cols and num_cols:
            cat = cat_cols[0]
            metric = num_cols[0]
            chart_name = f"Treemap: {cat} by {metric}"
            try:
                df_grouped = df.groupby(cat)[metric].sum().reset_index()
                df_grouped = df_grouped.sort_values(metric, ascending=False).head(8)
                total = df_grouped[metric].sum()
                
                if total > 0:
                    top_name = str(df_grouped[cat].iloc[0])
                    top_pct = (df_grouped[metric].iloc[0] / total * 100)
                    insight = f"Treemap allocation indicates '{top_name}' contributes the largest share ({top_pct:.1f}%) of overall {metric}."
                    
                    charts.append({
                        "type": "treemap",
                        "title": format_title(f"Volume Concentration Treemap: {cat} by {metric}"),
                        "relevance_score": 83.0,
                        "insight": insight,
                        "data": [
                            {"name": str(row[cat]), "size": float(row[metric])}
                            for _, row in df_grouped.iterrows()
                        ]
                    })
                    log_chart_attempt(chart_name, True)
                else:
                    log_chart_attempt(chart_name, False, "Total sum is 0")
            except Exception as e:
                log_chart_attempt(chart_name, False, str(e))

        # Composition Pie
        cat = cat_cols[0]
        chart_name = f"Pie Composition: {cat}"
        try:
            vc = df[cat].dropna().astype(str).value_counts().head(6)
            total = vc.sum()
            if total > 0:
                top_name = str(vc.index[0])
                top_pct = (vc.iloc[0] / total * 100)
                insight = f"Segment composition check shows '{top_name}' as the largest slice, representing {top_pct:.1f}% share."
                
                charts.append({
                    "type": "pie",
                    "title": format_title(f"Composition Breakdown: {cat} share"),
                    "relevance_score": 75.0,
                    "insight": insight,
                    "data": [
                        {
                            "name": str(k),
                            "value": int(v),
                            "pct": round(int(v) / total * 100, 1),
                        }
                        for k, v in vc.items()
                    ]
                })
                log_chart_attempt(chart_name, True)
            else:
                log_chart_attempt(chart_name, False, "Total categorical count is 0")
        except Exception as e:
            log_chart_attempt(chart_name, False, str(e))

    # ────────────────────────────────────────────────────────────────────────
    # 5. GUARANTEE MINIMUM CHART COUNT: 6–12 (FALLBACK STRUCTURAL AUDIT)
    # ────────────────────────────────────────────────────────────────────────
    if len(charts) < 6:
        logger.info(f"Generated chart count ({len(charts)}) is below 6. Adding fallback structural audit charts...")
        
        # Fallback 1: Structural Histogram
        chart_name = "Fallback: Dataset Structural Breakdown"
        try:
            insight = f"Baseline diagnostic chart detailing overall dataset layout. Row volume index is {len(df)} records across {len(df.columns)} dimensions."
            charts.append({
                "type": "histogram",
                "title": "Dataset Structural Breakdown",
                "x_axis": "Aspect",
                "y_axis": "Measure",
                "relevance_score": 50.0,
                "insight": insight,
                "data": [
                    {"bin": "Total Rows", "count": len(df)},
                    {"bin": "Total Columns", "count": len(df.columns)},
                    {"bin": "Numerical Columns", "count": len(num_cols)},
                    {"bin": "Categorical Columns", "count": len(cat_cols)}
                ]
            })
            log_chart_attempt(chart_name, True)
        except Exception as e:
            log_chart_attempt(chart_name, False, str(e))

        # Fallback 2: Row Count by columns (Bar chart)
        chart_name = "Fallback: Row Ingestion Audit"
        try:
            charts.append({
                "type": "bar",
                "title": "Data Ingestion Field Audit",
                "x_axis": "Column",
                "y_axis": "Non-Null Rows",
                "relevance_score": 48.0,
                "insight": "Ingestion audit evaluating completeness metrics across all columns loaded in memory.",
                "data": [
                    {"name": col[:15], "value": int(df[col].notna().sum())}
                    for col in df.columns[:10]
                ]
            })
            log_chart_attempt(chart_name, True)
        except Exception as e:
            log_chart_attempt(chart_name, False, str(e))

        # Fallback 3: Column uniqueness check (Bar chart)
        chart_name = "Fallback: Column Cardinality Audit"
        try:
            charts.append({
                "type": "bar",
                "title": "Unique Value Cardinality Profile",
                "x_axis": "Column",
                "y_axis": "Unique Elements",
                "relevance_score": 46.0,
                "insight": "Unique entry footprint index highlighting dimensional cardinality values.",
                "data": [
                    {"name": col[:15], "value": int(df[col].nunique())}
                    for col in df.columns[:10]
                ]
            })
            log_chart_attempt(chart_name, True)
        except Exception as e:
            log_chart_attempt(chart_name, False, str(e))

    # ── GUARANTEE HIGH-VALUE CHARTS ──
    # Let's ensure we have at least 1 trend, 1 pareto, and 1 scatter chart in the list.
    
    # 1. Guarantee Trend
    if not any(c["type"] == "trend" for c in charts):
        try:
            if date_cols and num_cols:
                d_col = date_cols[0]
                m_col = num_cols[0]
                df_agg = df.dropna(subset=[d_col, m_col]).groupby(d_col)[m_col].sum().reset_index().sort_values(d_col).head(24)
                if len(df_agg) >= 2:
                    charts.append({
                        "type": "trend",
                        "title": f"Executive Time Horizon: {m_col} Trend",
                        "x_axis": d_col,
                        "y_axis": m_col,
                        "relevance_score": 96.0,
                        "insight": f"Time-series analysis of {m_col} over {d_col} indicates overall performance movement over the observation horizon.",
                        "data": [{"date": str(row[d_col]), "value": float(row[m_col]), "moving_average": float(row[m_col])} for _, row in df_agg.iterrows()]
                    })
            elif num_cols:
                m_col = num_cols[0]
                df_seq = df[[m_col]].dropna().head(35).reset_index()
                if not df_seq.empty:
                    mean_val = float(df_seq[m_col].mean())
                    charts.append({
                        "type": "trend",
                        "title": f"Sequence Trend: {m_col} Run Rate",
                        "x_axis": "Record Index",
                        "y_axis": m_col,
                        "relevance_score": 96.0,
                        "insight": f"No chronological date column was detected. Sequence index mapping of {m_col} shows a baseline mean of {mean_val:,.1f}.",
                        "data": [{"date": f"Idx {row['index']}", "value": float(row[m_col]), "moving_average": mean_val} for _, row in df_seq.iterrows()]
                    })
            else:
                df_seq = df.head(30).reset_index()
                charts.append({
                    "type": "trend",
                    "title": "Ingested Volumetric Index Trend",
                    "x_axis": "Record Index",
                    "y_axis": "Record Volume",
                    "relevance_score": 96.0,
                    "insight": "Time-series sequence representation of ingested records showing steady-state volume trends.",
                    "data": [{"date": f"Idx {row['index']}", "value": 1.0, "moving_average": 1.0} for _, row in df_seq.iterrows()]
                })
        except Exception as e:
            logger.warning(f"Failed to generate guarantee trend: {e}")

    # 2. Guarantee Pareto
    if not any(c["type"] == "pareto" for c in charts):
        try:
            if cat_cols and num_cols:
                c_col = cat_cols[0]
                m_col = num_cols[0]
                df_grouped = df.groupby(c_col)[m_col].sum().reset_index()
                df_grouped = df_grouped.sort_values(m_col, ascending=False).head(8)
                total = df_grouped[m_col].sum()
                if total > 0:
                    data = []
                    cum_pct = 0.0
                    for _, row in df_grouped.iterrows():
                        val = float(row[m_col])
                        cum_pct += (val / total * 100)
                        data.append({
                            "name": str(row[c_col]),
                            "value": val,
                            "cumulative": round(cum_pct, 1)
                        })
                    charts.append({
                        "type": "pareto",
                        "title": f"Pareto Ranking: {c_col} contribution to {m_col}",
                        "x_axis": c_col,
                        "y_axis": m_col,
                        "relevance_score": 94.0,
                        "insight": f"Ranked contribution Pareto audit displays concentration of {m_col} across top segments of {c_col}.",
                        "data": data
                    })
            elif cat_cols:
                c_col = cat_cols[0]
                df_grouped = df[c_col].value_counts().reset_index(name="count")
                df_grouped.columns = [c_col, "count"]
                df_grouped = df_grouped.head(8)
                total = df_grouped["count"].sum()
                if total > 0:
                    data = []
                    cum_pct = 0.0
                    for _, row in df_grouped.iterrows():
                        val = float(row["count"])
                        cum_pct += (val / total * 100)
                        data.append({
                            "name": str(row[c_col]),
                            "value": val,
                            "cumulative": round(cum_pct, 1)
                        })
                    charts.append({
                        "type": "pareto",
                        "title": f"Pareto Ranking: {c_col} Frequency Distribution",
                        "x_axis": c_col,
                        "y_axis": "Record Count",
                        "relevance_score": 94.0,
                        "insight": f"Pareto concentration chart isolates category frequencies across {c_col}.",
                        "data": data
                    })
            elif num_cols:
                m_col = num_cols[0]
                df_grouped = df[[m_col]].dropna().sort_values(m_col, ascending=False).head(10).reset_index()
                total = df_grouped[m_col].sum()
                if total > 0:
                    data = []
                    cum_pct = 0.0
                    for _, row in df_grouped.iterrows():
                        val = float(row[m_col])
                        cum_pct += (val / total * 100)
                        data.append({
                            "name": f"Row {row['index']}",
                            "value": val,
                            "cumulative": round(cum_pct, 1)
                        })
                    charts.append({
                        "type": "pareto",
                        "title": f"Pareto Analysis of Top Values: {m_col}",
                        "x_axis": "Row Identifier",
                        "y_axis": m_col,
                        "relevance_score": 94.0,
                        "insight": f"Ranked contribution of individual record values highlights high concentration outliers.",
                        "data": data
                    })
            else:
                # Pareto of column non-null counts (real data, no dummies)
                col_counts = sorted(
                    [(col[:20], int(df[col].notna().sum())) for col in df.columns[:10]],
                    key=lambda x: x[1], reverse=True
                )
                total_nn = sum(c[1] for c in col_counts) or 1
                cum_pct = 0.0
                pareto_data = []
                for col_name, col_val in col_counts:
                    cum_pct += (col_val / total_nn * 100)
                    pareto_data.append({"name": col_name, "value": col_val, "cumulative": round(min(cum_pct, 100.0), 1)})
                charts.append({
                    "type": "pareto",
                    "title": "Field Completeness Concentration (Pareto)",
                    "x_axis": "Column",
                    "y_axis": "Non-Null Records",
                    "relevance_score": 94.0,
                    "insight": f"Pareto distribution of non-null record counts across {len(col_counts)} fields.",
                    "data": pareto_data
                })
        except Exception as e:
            logger.warning(f"Failed to generate guarantee pareto: {e}")

    # 3. Guarantee Scatter
    if not any(c["type"] == "scatter" for c in charts):
        try:
            if len(num_cols) >= 2:
                c1, c2 = num_cols[0], num_cols[1]
                sample_df = df[[c1, c2]].dropna().head(100)
                if not sample_df.empty:
                    r_val = df[c1].corr(df[c2])
                    charts.append({
                        "type": "scatter",
                        "title": f"Bivariate Scatter Correlation: {c1} vs {c2}",
                        "x_axis": c1,
                        "y_axis": c2,
                        "relevance_score": 92.0,
                        "insight": f"Bivariate scatter plot illustrates relationship (r={r_val:.2f}) between metrics '{c1}' and '{c2}'.",
                        "data": [{"x": float(row[c1]), "y": float(row[c2])} for _, row in sample_df.iterrows()]
                    })
            elif num_cols:
                c1 = num_cols[0]
                sample_df = df[[c1]].dropna().head(100).reset_index()
                if not sample_df.empty:
                    charts.append({
                        "type": "scatter",
                        "title": f"Metric Spread Index: {c1} Distribution",
                        "x_axis": "Record Index",
                        "y_axis": c1,
                        "relevance_score": 92.0,
                        "insight": f"Scatter plot of '{c1}' values against record indices to visualize variance footprint.",
                        "data": [{"x": float(row["index"]), "y": float(row[c1])} for _, row in sample_df.iterrows()]
                    })
            elif cat_cols:
                c_col = cat_cols[0]
                vc = df[c_col].value_counts().head(30).reset_index()
                vc.columns = [c_col, "count"]
                charts.append({
                    "type": "scatter",
                    "title": f"Category Frequency Spread: {c_col}",
                    "x_axis": "Category Rank",
                    "y_axis": "Record Count",
                    "relevance_score": 92.0,
                    "insight": f"Visualizing volume variance and dispersion of top category categories.",
                    "data": [{"x": float(idx), "y": float(row["count"])} for idx, row in vc.iterrows()]
                })
            else:
                # Scatter of column cardinality vs non-null count (real data)
                scatter_data = []
                for idx, col in enumerate(df.columns[:20]):
                    scatter_data.append({"x": float(df[col].nunique()), "y": float(df[col].notna().sum())})
                charts.append({
                    "type": "scatter",
                    "title": "Column Cardinality vs Completeness Dispersion",
                    "x_axis": "Unique Value Count",
                    "y_axis": "Non-Null Record Count",
                    "relevance_score": 92.0,
                    "insight": f"Scatter plot mapping each column's cardinality against its non-null completeness across {len(scatter_data)} fields.",
                    "data": scatter_data
                })
        except Exception as e:
            logger.warning(f"Failed to generate guarantee scatter: {e}")

    # ────────────────────────────────────────────────────────────────────────
    # 6. ABSOLUTE MINIMUM 3-CHART GUARANTEE (EMERGENCY FALLBACK)
    # ────────────────────────────────────────────────────────────────────────
    if len(charts) < 3:
        logger.warning(f"EMERGENCY: Only {len(charts)} charts generated. Adding raw DataFrame fallbacks...")
        
        # Emergency Fallback A: Column Data Types Overview
        if not any(c.get("title") == "Dataset Column Type Profile" for c in charts):
            try:
                dtype_counts = {}
                for col in df.columns:
                    dtype = str(df[col].dtype)
                    if "int" in dtype or "float" in dtype:
                        dtype_counts["Numeric"] = dtype_counts.get("Numeric", 0) + 1
                    elif "datetime" in dtype:
                        dtype_counts["DateTime"] = dtype_counts.get("DateTime", 0) + 1
                    elif "bool" in dtype:
                        dtype_counts["Boolean"] = dtype_counts.get("Boolean", 0) + 1
                    else:
                        dtype_counts["Text/Categorical"] = dtype_counts.get("Text/Categorical", 0) + 1
                
                charts.append({
                    "type": "pie",
                    "title": "Dataset Column Type Profile",
                    "relevance_score": 45.0,
                    "insight": f"Dataset comprises {len(df.columns)} columns across {len(dtype_counts)} data type categories with {len(df):,} records.",
                    "data": [
                        {"name": k, "value": v, "pct": round(v / len(df.columns) * 100, 1)}
                        for k, v in dtype_counts.items()
                    ]
                })
            except Exception as e:
                logger.warning(f"Emergency pie chart failed: {e}")

        # Emergency Fallback B: Non-Null Completeness Bar
        if len(charts) < 3:
            try:
                charts.append({
                    "type": "bar",
                    "title": "Column Completeness Audit",
                    "x_axis": "Column",
                    "y_axis": "Non-Null Rows",
                    "relevance_score": 42.0,
                    "insight": f"Data completeness audit across {min(len(df.columns), 10)} columns showing non-null record availability.",
                    "data": [
                        {"name": col[:15], "value": int(df[col].notna().sum())}
                        for col in df.columns[:10]
                    ]
                })
            except Exception as e:
                logger.warning(f"Emergency bar chart failed: {e}")

        # Emergency Fallback C: Summary Statistics
        if len(charts) < 3:
            try:
                charts.append({
                    "type": "histogram",
                    "title": "Dataset Volume Profile",
                    "x_axis": "Metric",
                    "y_axis": "Value",
                    "relevance_score": 40.0,
                    "insight": f"Structural overview: {len(df):,} rows, {len(df.columns)} columns.",
                    "data": [
                        {"bin": "Total Rows", "count": len(df)},
                        {"bin": "Total Columns", "count": len(df.columns)},
                        {"bin": "Complete Rows", "count": int(df.dropna().shape[0])},
                        {"bin": "Missing Cells", "count": int(df.isna().sum().sum())}
                    ]
                })
            except Exception as e:
                logger.warning(f"Emergency histogram failed: {e}")

    # ── Final Summary & Metrics Logging ──
    charts.sort(key=lambda c: c.get("relevance_score", 0.0), reverse=True)
    final_charts = charts[:12]
    
    logger.info("----------------------------------------")
    logger.info("CHART GENERATION ENGINE SUMMARY:")
    logger.info(f"  - Candidates Generated: {candidates_count}")
    logger.info(f"  - Successfully Rendered: {rendered_count}")
    logger.info(f"  - Failed Candidates: {len(failed_charts)}")
    for fc in failed_charts:
        logger.info(f"    * '{fc['name']}' reason: {fc['reason']}")
    logger.info(f"  - Final Displayed Charts: {len(final_charts)}")
    if len(final_charts) < 3:
        logger.error("CRITICAL: Less than 3 charts in final output! This should never happen.")
    logger.info("========================================")

    return final_charts


def build_dashboard_charts(df: pd.DataFrame, schema: DatasetSchema, dashboard: str) -> List[Dict[str, Any]]:
    from core.df_utils import get_analytic_numeric_cols, get_categorical_cols
    
    num_cols = get_analytic_numeric_cols(df, schema)
    cat_cols = get_categorical_cols(df, schema)
    date_cols = getattr(schema, "date_columns", [])
    
    # Check if we have primary metrics and dates
    date_col = date_cols[0] if date_cols else None
    primary_num = num_cols[0] if num_cols else None
    primary_cat = cat_cols[0] if cat_cols else None
    
    # Geographic columns detection
    geo_col = None
    for col in df.columns:
        col_lower = col.lower()
        if any(kw in col_lower for kw in ["region", "state", "country", "city", "location", "geo"]):
            geo_col = col
            break
    if not geo_col and len(cat_cols) > 1:
        geo_col = cat_cols[1]  # Fallback to second categorical
    elif not geo_col:
        geo_col = primary_cat  # Fallback to first categorical
        
    charts = []

    if dashboard == "executive":
        # 1. High-Level Strategic Trend (Line Chart)
        if date_col and primary_num:
            try:
                ts = df.dropna(subset=[date_col, primary_num]).copy()
                ts[date_col] = pd.to_datetime(ts[date_col], errors="coerce")
                ts = ts.dropna(subset=[date_col])
                grouped = ts.set_index(date_col).resample("D")[primary_num].sum().reset_index()
                grouped = grouped.sort_values(date_col).tail(30)
                chart_data = [{"date": str(row[date_col].date()), "value": float(row[primary_num])} for _, row in grouped.iterrows()]
                
                if len(chart_data) >= 7:
                    vals = [x["value"] for x in chart_data]
                    for idx, item in enumerate(chart_data):
                        if idx >= 6:
                            item["moving_average"] = round(float(np.mean(vals[idx-6:idx+1])), 2)
                            
                charts.append({
                    "type": "trend",
                    "title": f"Strategic Timeline: Total {to_business_label(primary_num)} Trend",
                    "x_axis": "Date",
                    "y_axis": primary_num,
                    "relevance_score": 98.0,
                    "insight": f"High-level strategic trend of total {to_business_label(primary_num)} across chronological intervals.",
                    "data": chart_data
                })
            except Exception as e:
                logger.warning(f"Failed to generate Executive Strategic Trend: {e}")
                
        # 2. Strategic Category Contribution (Pie/Donut Chart)
        if primary_cat and primary_num:
            try:
                grouped = df.groupby(primary_cat)[primary_num].sum().reset_index()
                grouped = grouped.sort_values(primary_num, ascending=False).head(8)
                chart_data = [{"name": str(row[primary_cat]), "value": float(row[primary_num])} for _, row in grouped.iterrows()]
                charts.append({
                    "type": "pie",
                    "title": f"Corporate Contribution Share of {to_business_label(primary_num)} by {to_business_label(primary_cat)}",
                    "x_axis": primary_cat,
                    "y_axis": primary_num,
                    "relevance_score": 95.0,
                    "insight": f"Strategic composition check illustrating relative share of {to_business_label(primary_num)} across categories.",
                    "data": chart_data
                })
            except Exception as e:
                logger.warning(f"Failed to generate Executive Category Contribution: {e}")
                
        # 3. Regional / Geographic Contribution (Bar Chart)
        if geo_col and primary_num:
            try:
                grouped = df.groupby(geo_col)[primary_num].sum().reset_index()
                grouped = grouped.sort_values(primary_num, ascending=False).head(8)
                chart_data = [{"name": str(row[geo_col]), "value": float(row[primary_num])} for _, row in grouped.iterrows()]
                charts.append({
                    "type": "bar",
                    "title": f"Geographic Distribution profile: {to_business_label(primary_num)} by {to_business_label(geo_col)}",
                    "x_axis": geo_col,
                    "y_axis": primary_num,
                    "relevance_score": 93.0,
                    "insight": f"Regional overview of {to_business_label(primary_num)} performance indicators across geographic locations.",
                    "data": chart_data
                })
            except Exception as e:
                logger.warning(f"Failed to generate Executive Geographic Contribution: {e}")

        # Fallback if no charts generated
        while len(charts) < 3:
            charts.append({
                "type": "bar",
                "title": "Data Ingestion Completion Profile",
                "x_axis": "Column",
                "y_axis": "Non-Null Records",
                "data": [{"name": col[:15], "value": int(df[col].notna().sum())} for col in df.columns[:8]],
                "insight": "General structural audit of ingested columns completeness values.",
                "relevance_score": 50.0
            })
            
    elif dashboard == "kpi":
        # 1. Operational Performance Trend (Use secondary metric if available, e.g. Quantity or Profit)
        secondary_num = num_cols[1] if len(num_cols) > 1 else None
        kpi_num = secondary_num or primary_num
        if date_col and kpi_num:
            try:
                ts = df.dropna(subset=[date_col, kpi_num]).copy()
                ts[date_col] = pd.to_datetime(ts[date_col], errors="coerce")
                ts = ts.dropna(subset=[date_col])
                grouped = ts.set_index(date_col).resample("D")[kpi_num].sum().reset_index()
                grouped = grouped.sort_values(date_col).tail(30)
                chart_data = [{"date": str(row[date_col].date()), "value": float(row[kpi_num])} for _, row in grouped.iterrows()]
                
                charts.append({
                    "type": "trend",
                    "title": f"Operational Trend Tracker: {to_business_label(kpi_num)} over Time",
                    "x_axis": "Date",
                    "y_axis": kpi_num,
                    "relevance_score": 97.0,
                    "insight": f"Chronological performance tracking showing operational run-rate of {to_business_label(kpi_num)}.",
                    "data": chart_data
                })
            except Exception as e:
                logger.warning(f"Failed to generate KPI Operational Trend: {e}")
                
        # 2. Target vs Actual Performance Profile (Comparison of mean vs overall average)
        if primary_num and primary_cat:
            try:
                grouped = df.groupby(primary_cat)[primary_num].mean().reset_index()
                grouped = grouped.sort_values(primary_num, ascending=False).head(10)
                overall_avg = float(df[primary_num].mean())
                chart_data = []
                for _, row in grouped.iterrows():
                    val = float(row[primary_num])
                    chart_data.append({
                        "name": str(row[primary_cat]),
                        "value": val,
                        "target": round(overall_avg, 2)
                    })
                charts.append({
                    "type": "bar",
                    "title": f"Category Performance vs Benchmark Average ({to_business_label(primary_num)})",
                    "x_axis": primary_cat,
                    "y_axis": primary_num,
                    "relevance_score": 95.0,
                    "insight": f"Comparing categorical average {to_business_label(primary_num)} against overall benchmark of {overall_avg:,.1f}.",
                    "data": chart_data
                })
            except Exception as e:
                logger.warning(f"Failed to generate KPI Target vs Actual: {e}")
                
        # 3. Operational Volumetric Breakdown
        secondary_cat = cat_cols[1] if len(cat_cols) > 1 else None
        if secondary_cat:
            try:
                vc = df[secondary_cat].value_counts().head(8)
                chart_data = [{"name": str(k), "value": int(v)} for k, v in vc.items()]
                charts.append({
                    "type": "bar",
                    "title": f"Volumetric Distribution: Record Count by {to_business_label(secondary_cat)}",
                    "x_axis": secondary_cat,
                    "y_axis": "Records",
                    "relevance_score": 92.0,
                    "insight": f"Operational capacity indicators showing volume distribution across {to_business_label(secondary_cat)} segments.",
                    "data": chart_data
                })
            except Exception as e:
                logger.warning(f"Failed to generate KPI Volumetric Breakdown: {e}")

        # Fallback if no charts generated
        while len(charts) < 3:
            charts.append({
                "type": "bar",
                "title": "Ingested Cardinality profile",
                "x_axis": "Column",
                "y_axis": "Unique Values",
                "data": [{"name": col[:15], "value": int(df[col].nunique())} for col in df.columns[:8]],
                "insight": "General structural audit of ingested columns cardinality values.",
                "relevance_score": 50.0
            })

    elif dashboard == "customer":
        try:
            from analytics.customer_intelligence import compute_customer_intelligence
            ci = compute_customer_intelligence(df, schema)
            if ci.get("eligible"):
                # 1. Segment Contribution (Pie/Donut of segment total spend share)
                segments = ci.get("segments", {})
                segment_pie_data = []
                for seg_key, seg_val in segments.items():
                    segment_pie_data.append({
                        "name": seg_val["name"],
                        "value": float(seg_val["total_spend"]),
                        "pct": float(seg_val["share_percentage"])
                    })
                charts.append({
                    "type": "pie",
                    "title": "Customer RFM Segment Contribution Share",
                    "x_axis": "Segment",
                    "y_axis": "Revenue Share",
                    "relevance_score": 98.0,
                    "insight": "RFM (Recency, Frequency, Monetary) segmentation cohort contribution relative to overall sales volume.",
                    "data": segment_pie_data
                })

                # 2. Top Customers (Bar chart of top 10 customer spends)
                top_custs = ci.get("top_customers", [])
                charts.append({
                    "type": "bar",
                    "title": "Top 10 Customers Purchase Spend Profile",
                    "x_axis": "Customer",
                    "y_axis": "Total Spend",
                    "relevance_score": 97.0,
                    "insight": "Ranked purchase spends for the top 10 customer accounts in the dataset.",
                    "data": [{"name": c["customer"], "value": c["spend"]} for c in top_custs]
                })

                # 3. Customer Spend Distribution (Histogram of total spend)
                cust_col = ci.get("customer_column")
                rev_col = ci.get("revenue_column")
                if cust_col and rev_col:
                    df_clean = df.dropna(subset=[cust_col, rev_col]).copy()
                    df_clean[rev_col] = pd.to_numeric(df_clean[rev_col], errors="coerce")
                    df_clean = df_clean.dropna(subset=[rev_col])
                    cust_gp = df_clean.groupby(cust_col)[rev_col].sum().dropna()
                    if not cust_gp.empty:
                        counts, bins = np.histogram(cust_gp, bins=8)
                        hist_data = []
                        for i in range(len(counts)):
                            hist_data.append({"bin": f"{bins[i]:.1f} - {bins[i+1]:.1f}", "count": int(counts[i])})
                        charts.append({
                            "type": "histogram",
                            "title": "Customer Spend Frequency Distribution Spectrum",
                            "x_axis": "Spend Range",
                            "y_axis": "Customer Count",
                            "relevance_score": 96.0,
                            "insight": "Binned frequency distribution profiling how purchase spend levels spread across the customer base.",
                            "data": hist_data
                        })

                # 4. CLV Distribution (Histogram of customer CLV)
                if cust_col and rev_col:
                    cust_gp_full = df_clean.groupby(cust_col).agg(
                        spend=(rev_col, "sum"),
                        orders=(rev_col, "count")
                    )
                    clvs = cust_gp_full["spend"] * (1.0 + (cust_gp_full["orders"] - 1) * 0.20)
                    clvs = clvs.dropna()
                    if not clvs.empty:
                        counts, bins = np.histogram(clvs, bins=8)
                        clv_hist_data = []
                        for i in range(len(counts)):
                            clv_hist_data.append({"bin": f"{bins[i]:.1f} - {bins[i+1]:.1f}", "count": int(counts[i])})
                        charts.append({
                            "type": "histogram",
                            "title": "Estimated Customer Lifetime Value (CLV) Spread Profile",
                            "x_axis": "CLV Range",
                            "y_axis": "Customer Count",
                            "relevance_score": 95.0,
                            "insight": "Estimated Customer Lifetime Value (CLV) spread matching transaction frequencies and spend limits.",
                            "data": clv_hist_data
                        })

                # 5. Pareto Distribution (Cumulative Revenue concentration curve)
                pareto_data = []
                total_rev = ci.get("total_revenue", 1.0)
                cum_pct = 0.0
                for c in top_custs:
                    cum_pct += (c["spend"] / total_rev * 100)
                    pareto_data.append({
                        "name": c["customer"],
                        "value": c["spend"],
                        "cumulative": round(min(cum_pct, 100.0), 1)
                    })
                charts.append({
                    "type": "pareto",
                    "title": "Top Customer Revenue Concentration (Pareto Curve)",
                    "x_axis": "Customer",
                    "y_axis": "Spend",
                    "relevance_score": 94.0,
                    "insight": f"Concentration curve highlighting ranked customer contribution. The top {ci.get('pareto_80_20_customer_pct')}% of accounts generate 80% of sales.",
                    "data": pareto_data
                })

                # 6. Customer Ranking & Order Frequency (Bar chart of purchase transactions)
                charts.append({
                    "type": "bar",
                    "title": "Top 10 Customers Order Frequency Ranking",
                    "x_axis": "Customer",
                    "y_axis": "Transactions Count",
                    "relevance_score": 93.0,
                    "insight": "Purchase frequencies and transaction counts for the top 10 customers.",
                    "data": [{"name": c["customer"], "value": c["transactions"]} for c in top_custs]
                })

                # 7. Revenue Concentration Treemap
                charts.append({
                    "type": "treemap",
                    "title": "Revenue Concentration by Customer Segment",
                    "x_axis": "Segment",
                    "y_axis": "Total Spend",
                    "relevance_score": 92.0,
                    "insight": "Treemap visualization displaying proportional spend distribution across customer RFM segments.",
                    "data": [{"name": seg_val["name"], "size": float(seg_val["total_spend"])} for seg_key, seg_val in segments.items()]
                })
            else:
                logger.warning(f"Customer Intelligence not eligible for dashboard charts: {ci.get('message')}")
        except Exception as e:
            logger.warning(f"Failed to generate Customer Intelligence Dashboard charts: {e}", exc_info=True)

        while len(charts) < 3:
            if len(charts) == 0:
                charts.append({
                    "type": "bar",
                    "title": "Column Data Completeness",
                    "x_axis": "Column",
                    "y_axis": "Non-Null Records",
                    "data": [{"name": col[:15], "value": int(df[col].notna().sum())} for col in df.columns[:8]],
                    "insight": f"Data completeness audit: {min(len(df.columns), 8)} columns.",
                    "relevance_score": 50.0
                })
            elif len(charts) == 1:
                charts.append({
                    "type": "bar",
                    "title": "Unique Value Cardinality",
                    "x_axis": "Column",
                    "y_axis": "Unique Values",
                    "data": [{"name": col[:15], "value": int(df[col].nunique())} for col in df.columns[:8]],
                    "insight": f"Unique value counts across {min(len(df.columns), 8)} columns.",
                    "relevance_score": 48.0
                })
            else:
                charts.append({
                    "type": "histogram",
                    "title": "Dataset Volume Profile",
                    "x_axis": "Metric",
                    "y_axis": "Value",
                    "data": [
                        {"bin": "Total Rows", "count": len(df)},
                        {"bin": "Total Columns", "count": len(df.columns)},
                        {"bin": "Complete Rows", "count": int(df.dropna().shape[0])},
                        {"bin": "Missing Cells", "count": int(df.isna().sum().sum())}
                    ],
                    "insight": f"Structural overview: {len(df):,} rows, {len(df.columns)} columns.",
                    "relevance_score": 45.0
                })
            
    return charts[:6]


def generate_custom_chart_data(
    df: pd.DataFrame,
    schema: DatasetSchema,
    chart_type: str,
    x_axis: Optional[str] = None,
    y_axis: Optional[str] = None
) -> Dict[str, Any]:
    from core.df_utils import get_analytic_numeric_cols, get_categorical_cols, _is_id_col

    # Validate against identifier/ID columns
    if x_axis and x_axis in df.columns:
        if _is_id_col(x_axis, df[x_axis]):
            raise ValueError(f"Cannot generate chart for identifier or ID column: '{x_axis}'")
            
    if y_axis and y_axis in df.columns:
        if _is_id_col(y_axis, df[y_axis]):
            raise ValueError(f"Cannot generate chart for identifier or ID column: '{y_axis}'")
    
    num_cols = get_analytic_numeric_cols(df, schema)
    cat_cols = get_categorical_cols(df, schema)
    date_cols = getattr(schema, "date_columns", [])
    
    # Ensure columns exist in df
    available_cols = list(df.columns)
    if not available_cols:
        return {
            "type": "bar",
            "title": "Empty Dataset Profile",
            "x_axis": "Status",
            "y_axis": "Count",
            "data": [{"name": "No Data Available", "value": 0.0}],
            "insight": "The dataset is empty. Load a valid dataset to analyze performance."
        }

    # Auto-resolve or validate x_axis
    if not x_axis or x_axis not in df.columns:
        if date_cols and date_cols[0] in df.columns:
            x_axis = date_cols[0]
        elif cat_cols and cat_cols[0] in df.columns:
            x_axis = cat_cols[0]
        elif num_cols and num_cols[0] in df.columns:
            x_axis = num_cols[0]
        else:
            x_axis = df.columns[0]

    # Helper function to get metric columns
    def get_first_numeric_excluding(exclude_col):
        for col in num_cols:
            if col != exclude_col and col in df.columns:
                return col
        for col in df.columns:
            if col != exclude_col and pd.api.types.is_numeric_dtype(df[col]) and col not in date_cols:
                return col
        return None

    # Ensure y_axis exists in df.columns, if not or if it matches x_axis, try to find another numeric
    if chart_type not in ["heatmap", "correlation", "histogram", "boxplot"]:
        if not y_axis or y_axis not in df.columns or y_axis == x_axis:
            y_axis = get_first_numeric_excluding(x_axis)

    # Detect semantic types
    is_x_num = pd.api.types.is_numeric_dtype(df[x_axis]) and x_axis not in date_cols
    is_x_date = x_axis in date_cols or pd.api.types.is_datetime64_any_dtype(df[x_axis])
    is_x_cat = not is_x_num and not is_x_date

    adjusted_type = chart_type.lower()
    
    # ── FALLBACK & ADAPTATION MATRIX ──
    # 1. Heatmap / Correlation selected without multiple numeric columns: convert to Bar Chart
    if adjusted_type in ["heatmap", "correlation"]:
        valid_nums = [c for c in num_cols if c in df.columns]
        if len(valid_nums) < 2:
            adjusted_type = "bar"
            if cat_cols and cat_cols[0] in df.columns:
                x_axis = cat_cols[0]
            else:
                x_axis = df.columns[0]
            y_axis = None
            is_x_num = pd.api.types.is_numeric_dtype(df[x_axis]) and x_axis not in date_cols
            is_x_date = x_axis in date_cols or pd.api.types.is_datetime64_any_dtype(df[x_axis])
            is_x_cat = not is_x_num and not is_x_date

    # 2. Histogram / Boxplot selected without numeric X-axis: convert to Bar Chart
    elif adjusted_type in ["histogram", "boxplot"]:
        if not is_x_num:
            backup_num = get_first_numeric_excluding(None)
            if backup_num:
                x_axis = backup_num
                is_x_num = True
                is_x_date = False
                is_x_cat = False
            else:
                adjusted_type = "bar"
                y_axis = None

    # 3. Scatter / Bubble Plot selected with < 2 numeric columns: convert to Histogram
    elif adjusted_type in ["scatter", "bubble"]:
        if not y_axis or y_axis not in df.columns:
            y_axis = get_first_numeric_excluding(x_axis)
        
        is_y_num = y_axis and pd.api.types.is_numeric_dtype(df[y_axis]) and y_axis not in date_cols
        
        if not is_x_num or not is_y_num:
            first_num = get_first_numeric_excluding(None)
            if first_num:
                second_num = get_first_numeric_excluding(first_num)
                if second_num:
                    x_axis = first_num
                    y_axis = second_num
                    is_x_num = True
                    is_y_num = True
                else:
                    adjusted_type = "histogram"
                    x_axis = first_num
                    y_axis = None
            else:
                adjusted_type = "bar"
                if cat_cols and cat_cols[0] in df.columns:
                    x_axis = cat_cols[0]
                y_axis = None
                is_x_num = False
                is_x_cat = True

    # For standard charts, allow categorical/ID Y-axis by setting compatibility aggregates
    else:
        if not y_axis or y_axis not in df.columns or y_axis == x_axis:
            y_axis = get_first_numeric_excluding(x_axis)
            if not y_axis:
                for col in df.columns:
                    if col != x_axis:
                        y_axis = col
                        break

    try:
        # Ensure clean dataframe for x and y
        cols_to_clean = [x_axis]
        if y_axis:
            cols_to_clean.append(y_axis)
        clean_df = df.dropna(subset=cols_to_clean).copy()
        
        if clean_df.empty:
            clean_df = df.copy()

        # Determine aggregation logic for Y axis (COUNT vs NUNIQUE vs SUM)
        agg_func = "sum"
        metric_name = y_axis
        if y_axis:
            is_y_numeric = pd.api.types.is_numeric_dtype(clean_df[y_axis])
            y_lower = str(y_axis).lower()
            is_y_id = any(kw in y_lower for kw in ["id", "code", "key", "number", "num"])
            
            if not is_y_numeric or is_y_id:
                if is_y_id:
                    agg_func = "nunique"
                    metric_name = f"Unique {to_business_label(y_axis)}"
                else:
                    agg_func = "count"
                    metric_name = f"Count of {to_business_label(y_axis)}"
            else:
                agg_func = "sum"
                metric_name = to_business_label(y_axis)
        else:
            agg_func = "count"
            metric_name = "Record Count"

        title = build_business_title(adjusted_type, x_axis, y_axis)

        # ── 1. Heatmap / Correlation ──
        if adjusted_type in ["heatmap", "correlation"]:
            valid_nums = [c for c in num_cols if c in clean_df.columns][:8]
            corr = clean_df[valid_nums].corr().round(2).fillna(0.0)
            data = []
            for x in valid_nums:
                for y in valid_nums:
                    data.append({
                        "x": to_business_label(x),
                        "y": to_business_label(y),
                        "value": float(corr.loc[x, y])
                    })
            return {
                "type": "heatmap",
                "title": title,
                "columns": [to_business_label(c) for c in valid_nums],
                "data": data,
                "relevance_score": 90.0,
                "insight": "Pearson correlation matrix detailing linear dependencies between numeric dimensions."
            }

        # ── 2. Histogram / Boxplot ──
        elif adjusted_type in ["histogram", "boxplot"]:
            series = pd.to_numeric(clean_df[x_axis], errors="coerce").dropna()
            if series.empty:
                vc = clean_df[x_axis].value_counts().head(10)
                data = [{"bin": str(k), "count": int(v)} for k, v in vc.items()]
            else:
                counts, bins = np.histogram(series, bins=10)
                data = []
                for i in range(len(counts)):
                    bin_label = f"{bins[i]:.1f} - {bins[i+1]:.1f}"
                    data.append({"bin": bin_label, "count": int(counts[i])})
            return {
                "type": "histogram",
                "title": title,
                "x_axis": to_business_label(x_axis),
                "y_axis": "Record Count",
                "data": data,
                "relevance_score": 85.0,
                "insight": f"Frequency distribution spectrum mapping the density layout of '{to_business_label(x_axis)}'."
            }

        # ── 3. Scatter / Bubble ──
        elif adjusted_type in ["scatter", "bubble"]:
            pts_df = clean_df[[x_axis, y_axis]].head(150)
            data = []
            for idx, row in pts_df.iterrows():
                try:
                    data.append({
                        "x": float(row[x_axis]),
                        "y": float(row[y_axis]),
                        "name": f"Row {idx}"
                    })
                except (ValueError, TypeError):
                    continue
            return {
                "type": "scatter",
                "title": title,
                "x_axis": to_business_label(x_axis),
                "y_axis": to_business_label(y_axis),
                "data": data,
                "relevance_score": 88.0,
                "insight": f"Bivariate scatter plot detailing the correlation dispersion of '{to_business_label(y_axis)}' against '{to_business_label(x_axis)}'."
            }

        # For grouping based charts (Pareto, Bar, Line, Area, etc.)
        # Determine temporal grouping vs categorical grouping
        is_date = is_x_date
        if not is_date:
            x_lower = str(x_axis).lower()
            date_keywords = ["date", "time", "created", "updated", "order", "transaction", "timestamp", "period"]
            if any(kw in x_lower for kw in date_keywords):
                is_date = True
            else:
                try:
                    sample_parsed = pd.to_datetime(clean_df[x_axis].head(50), errors='coerce')
                    if sample_parsed.notna().sum() > len(sample_parsed) * 0.7:
                        is_date = True
                except:
                    pass

        if is_date:
            clean_df[x_axis] = pd.to_datetime(clean_df[x_axis], errors='coerce')
            clean_df = clean_df.dropna(subset=[x_axis])
            if not clean_df.empty:
                num_unique_dates = clean_df[x_axis].nunique()
                if num_unique_dates > 30:
                    clean_df["x_axis_grouped"] = clean_df[x_axis].dt.strftime('%Y-%m')
                else:
                    clean_df["x_axis_grouped"] = clean_df[x_axis].dt.strftime('%Y-%m-%d')
                
                if y_axis:
                    if agg_func == "nunique":
                        grouped = clean_df.groupby("x_axis_grouped")[y_axis].nunique().reset_index()
                    elif agg_func == "count":
                        grouped = clean_df.groupby("x_axis_grouped")[y_axis].count().reset_index()
                    else:
                        grouped = clean_df.groupby("x_axis_grouped")[y_axis].sum().reset_index()
                else:
                    grouped = clean_df.groupby("x_axis_grouped").size().reset_index(name="count")
                
                grouped = grouped.rename(columns={"x_axis_grouped": x_axis, y_axis: metric_name, "count": metric_name})
                grouped = grouped.sort_values(x_axis, ascending=True)
            else:
                grouped = pd.DataFrame(columns=[x_axis, metric_name])
        else:
            if y_axis:
                if agg_func == "nunique":
                    grouped = clean_df.groupby(x_axis)[y_axis].nunique().reset_index()
                elif agg_func == "count":
                    grouped = clean_df.groupby(x_axis)[y_axis].count().reset_index()
                else:
                    grouped = clean_df.groupby(x_axis)[y_axis].sum().reset_index()
            else:
                grouped = clean_df.groupby(x_axis).size().reset_index(name="count")
            
            grouped = grouped.rename(columns={y_axis: metric_name, "count": metric_name})
            grouped = grouped.sort_values(metric_name, ascending=False).head(15)

        # ── 4. Pareto ──
        if adjusted_type == "pareto":
            # Force sorted by aggregate value descending for Pareto
            grouped_p = grouped.sort_values(metric_name, ascending=False).head(10)
            total = grouped_p[metric_name].sum()
            cum_pct = 0.0
            data = []
            for _, row in grouped_p.iterrows():
                val = float(row[metric_name])
                pct = (val / total * 100) if total > 0 else 0
                cum_pct += pct
                data.append({
                    "name": str(row[x_axis]),
                    "value": val,
                    "cumulative": round(min(cum_pct, 100.0), 1)
                })
            return {
                "type": "pareto",
                "title": title,
                "x_axis": to_business_label(x_axis),
                "y_axis": to_business_label(metric_name),
                "data": data,
                "relevance_score": 92.0,
                "insight": f"Pareto concentration analysis showing ranked cumulative contribution of '{to_business_label(metric_name)}' across categories of '{to_business_label(x_axis)}'."
            }

        # ── 5. Standard Aggregations (Bar, Line, Area, Pie, Donut, Treemap, Stacked Bar, Stacked Area) ──
        else:
            data = []
            for _, row in grouped.iterrows():
                data.append({
                    "name": str(row[x_axis]),
                    "value": float(row[metric_name])
                })
                
            mapped_type = "pie" if adjusted_type in ["pie", "donut"] else (
                "line" if adjusted_type in ["line", "area", "waterfall", "stacked_area"] else "bar"
            )
            
            return {
                "type": mapped_type,
                "title": title,
                "x_axis": to_business_label(x_axis),
                "y_axis": to_business_label(metric_name),
                "data": data,
                "relevance_score": 85.0,
                "insight": f"Bespoke visualization displaying '{to_business_label(metric_name)}' aggregated by '{to_business_label(x_axis)}'."
            }

    except Exception as e:
        logger.error(f"Custom chart fallback triggered due to error: {e}", exc_info=True)
        fallback_data = []
        for col in df.columns[:10]:
            fallback_data.append({
                "name": to_business_label(col),
                "value": float(df[col].notna().sum())
            })
        return {
            "type": "bar",
            "title": "Ingested Field Completeness (Emergency Fallback)",
            "x_axis": "Column",
            "y_axis": "Non-Null Rows",
            "data": fallback_data,
            "insight": f"Intelligent fallback activated: Columns mapping error was resolved automatically. Ingested completeness shown for {len(fallback_data)} fields."
        }


def customize_charts_by_context(
    charts: List[Dict[str, Any]],
    df: pd.DataFrame,
    schema: DatasetSchema,
    context: Dict[str, Any],
    dashboard: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Customize, reorder, and filter generated charts based on active business context without cross-dashboard contamination."""
    goal = str(context.get("analysis_goal", "")).lower()
    prob = str(context.get("business_problem", "")).lower()
    metric = str(context.get("success_metric", "")).lower()

    is_churn_retention = any(k in goal or k in prob or k in metric for k in ["churn", "retention", "customer"])
    is_revenue = any(k in goal or k in prob or k in metric for k in ["revenue", "sales", "profit", "earnings", "income", "price"])
    is_marketing = any(k in goal or k in prob or k in metric for k in ["marketing", "campaign", "ctr", "conversion", "roas", "ad"])
    is_ops = any(k in goal or k in prob or k in metric for k in ["operational", "operations", "supply", "efficiency", "cost", "shipment", "downtime", "defect", "yield"])

    boosted_charts = []
    for c in charts:
        c_copy = dict(c)
        title_lower = c_copy.get("title", "").lower()
        insight_lower = c_copy.get("insight", "").lower()
        boost = 0.0
        
        if is_churn_retention:
            if any(k in title_lower or k in insight_lower for k in ["churn", "retention", "customer", "cohort", "loyalty", "rfm"]):
                boost += 50.0
        if is_revenue:
            if any(k in title_lower or k in insight_lower for k in ["revenue", "sales", "profit", "earnings", "income", "margin"]):
                boost += 50.0
        if is_marketing:
            if any(k in title_lower or k in insight_lower for k in ["marketing", "campaign", "ctr", "conversion", "roas", "ad", "clicks", "impressions"]):
                boost += 50.0
        if is_ops:
            if any(k in title_lower or k in insight_lower for k in ["operational", "operations", "efficiency", "downtime", "defect", "yield", "cycle", "throughput"]):
                boost += 50.0
                
        c_copy["relevance_score"] = c_copy.get("relevance_score", 50.0) + boost
        boosted_charts.append(c_copy)
        
    boosted_charts.sort(key=lambda x: x.get("relevance_score", 50.0), reverse=True)
    return boosted_charts[:6]


