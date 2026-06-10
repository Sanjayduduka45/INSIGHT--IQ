"""
InsightIQ — Customer Intelligence Engine

Calculates RFM metrics (Recency, Frequency, Monetary), segments customers,
computes Customer Lifetime Value (CLV), Churn Risk, and Gini/Pareto concentration indices.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def compute_customer_intelligence(df: pd.DataFrame, schema: Any) -> Dict[str, Any]:
    """Analyzes customer contribution, repeat buyer rates, concentration, and segments."""
    
    # ── 1. RESOLVE COLUMNS ──────────────────────────────────────────────────
    cust_keywords = ["customer", "cust", "client", "member", "user", "buyer", "patient", "employee", "student"]
    cust_col = None
    for c in df.columns:
        if any(kw in c.lower() for kw in cust_keywords):
            cust_col = c
            break
            
    rev_keywords = ["revenue", "sales", "spend", "amount", "total", "price", "cost", "value"]
    rev_col = None
    for c in df.columns:
        if any(kw in c.lower() for kw in rev_keywords):
            rev_col = c
            break

    # Fallback heuristics
    from core.df_utils import get_categorical_cols, get_analytic_numeric_cols
    cats = get_categorical_cols(df, schema)
    nums = get_analytic_numeric_cols(df, schema)

    if not cust_col and cats:
        cust_col = cats[0]
    if not rev_col and nums:
        rev_col = nums[0]

    # If still missing, we cannot run customer intelligence
    if not cust_col or not rev_col:
        return {
            "eligible": False,
            "message": "Customer Intelligence requires a customer identifier column (e.g. Customer ID) and a numeric revenue/sales column."
        }

    try:
        # ── 2. CLEAN DATA ────────────────────────────────────────────────────
        df_clean = df.dropna(subset=[cust_col, rev_col]).copy()
        df_clean[rev_col] = pd.to_numeric(df_clean[rev_col], errors="coerce")
        df_clean = df_clean.dropna(subset=[rev_col])
        
        if len(df_clean) == 0:
            return {
                "eligible": False,
                "message": "Dataset contains zero rows with valid customer and revenue records."
            }

        # Date column for recency calculation
        has_dates = False
        date_col = None
        if schema.date_columns:
            date_col = schema.date_columns[0]
            if date_col in df_clean.columns:
                df_clean["_dt"] = pd.to_datetime(df_clean[date_col], errors="coerce")
                df_clean = df_clean.dropna(subset=["_dt"])
                if len(df_clean) > 0:
                    has_dates = True

        # ── 3. GROUP AND AGGREGATE RFM METRICS ────────────────────────────────
        if has_dates:
            overall_max_date = df_clean["_dt"].max()
            cust_group = df_clean.groupby(cust_col).agg(
                total_spend=(rev_col, "sum"),
                order_count=(rev_col, "count"),
                max_date=("_dt", "max")
            ).reset_index()
            cust_group["recency_days"] = (overall_max_date - cust_group["max_date"]).dt.days
        else:
            cust_group = df_clean.groupby(cust_col).agg(
                total_spend=(rev_col, "sum"),
                order_count=(rev_col, "count")
            ).reset_index()
            cust_group["recency_days"] = 0

        cust_group.columns = ["customer", "total_spend", "order_count"] + (["max_date", "recency_days"] if has_dates else ["recency_days"])
        total_revenue = float(cust_group["total_spend"].sum())
        total_customers = len(cust_group)

        if total_customers == 0 or total_revenue == 0:
            return {"eligible": False, "message": "Zero total customer volume or spend detected."}

        # Sort descending by spend
        cust_group = cust_group.sort_values("total_spend", ascending=False).reset_index(drop=True)

        # ── 4. RFM SCORE ASSIGNMENTS ──────────────────────────────────────────
        # Quintiles assignment using rank percentages to avoid qcut duplicate bin limits
        def assign_scores(series: pd.Series, reverse: bool = False) -> pd.Series:
            if len(series) < 5:
                # small dataset fallback: map values directly
                return pd.Series([3] * len(series), index=series.index)
            ranks = series.rank(pct=True, method="first")
            if reverse:
                return 5 - (ranks * 5).astype(int)
            else:
                return (ranks * 5).astype(int) + 1

        cust_group["m_score"] = assign_scores(cust_group["total_spend"], reverse=False)
        cust_group["f_score"] = assign_scores(cust_group["order_count"], reverse=False)
        
        if has_dates:
            cust_group["r_score"] = assign_scores(cust_group["recency_days"], reverse=True)
        else:
            cust_group["r_score"] = 5  # default to recent if no dates

        # ── 5. RFM SEGMENT MAPPINGS ───────────────────────────────────────────
        segments_list = []
        for _, row in cust_group.iterrows():
            r, f, m = row["r_score"], row["f_score"], row["m_score"]
            if r >= 4 and f >= 4 and m >= 4:
                seg = "Champions"
            elif r >= 3 and f >= 3 and m >= 3:
                seg = "Loyal Customers"
            elif r >= 3 and f >= 2:
                seg = "Potential Loyalists"
            elif r <= 2 and (f >= 3 or m >= 3):
                seg = "At Risk"
            elif r <= 2 and f <= 2 and m <= 2:
                seg = "Lost Customers"
            else:
                seg = "Needs Attention"
            segments_list.append(seg)
            
        cust_group["segment"] = segments_list

        # Calculate Churn Risk (0% - 100%)
        churn_list = []
        for _, row in cust_group.iterrows():
            r = row["r_score"]
            f = row["order_count"]
            if r <= 1:
                churn = 95.0
            elif r == 2:
                churn = 75.0
            elif r == 3:
                churn = 45.0
            else:
                churn = 15.0 if f > 1 else 30.0
            churn_list.append(churn)
        cust_group["churn_risk"] = churn_list

        # Calculate Customer Lifetime Value (CLV)
        # Formula: Spend * (1 + Repeat purchase coefficient)
        cust_group["clv"] = cust_group["total_spend"] * (1.0 + (cust_group["order_count"] - 1) * 0.20)

        # ── 6. SEGMENT AGGREGATIONS ───────────────────────────────────────────
        seg_names = ["Champions", "Loyal Customers", "Potential Loyalists", "At Risk", "Lost Customers", "Needs Attention"]
        segments_stats = {}
        for idx, name in enumerate(seg_names):
            sub = cust_group[cust_group["segment"] == name]
            spend_sum = float(sub["total_spend"].sum())
            segments_stats[name.lower().replace(" ", "_")] = {
                "name": name,
                "customer_count": len(sub),
                "total_spend": spend_sum,
                "average_spend": float(sub["total_spend"].mean()) if len(sub) > 0 else 0.0,
                "share_percentage": round((spend_sum / total_revenue) * 100, 1) if total_revenue > 0 else 0.0
            }

        # ── 7. PARETO 80/20 REVENUE RULE ──────────────────────────────────────
        cust_group["cum_spend"] = cust_group["total_spend"].cumsum()
        target_80 = total_revenue * 0.8
        customers_to_80 = int((cust_group["cum_spend"] <= target_80).sum()) + 1
        pareto_pct = (customers_to_80 / total_customers) * 100 if total_customers > 0 else 0.0

        # Pareto 10% & 20% concentration
        top_10_count = max(1, int(total_customers * 0.1))
        top_20_count = max(1, int(total_customers * 0.2))
        concentration_10 = (cust_group.head(top_10_count)["total_spend"].sum() / total_revenue) * 100
        concentration_20 = (cust_group.head(top_20_count)["total_spend"].sum() / total_revenue) * 100

        # Repeat Buyers rate
        repeat_buyers = cust_group[cust_group["order_count"] > 1]
        repeat_count = len(repeat_buyers)
        repeat_rate = (repeat_count / total_customers) * 100
        repeat_revenue_share = (repeat_buyers["total_spend"].sum() / total_revenue) * 100

        # ── 8. TOP 10 LIST ───────────────────────────────────────────────────
        top_list = []
        for i, row in cust_group.head(10).iterrows():
            top_list.append({
                "rank": i + 1,
                "customer": str(row["customer"]),
                "spend": float(row["total_spend"]),
                "share": round((row["total_spend"] / total_revenue) * 100, 2),
                "transactions": int(row["order_count"]),
                "segment": row["segment"],
                "clv": round(float(row["clv"]), 2),
                "churn_risk": float(row["churn_risk"]),
                "recency": int(row["recency_days"])
            })

        # ── 9. RULE-BASED INSIGHT GENERATION ─────────────────────────────────
        champions_pct = segments_stats["champions"]["share_percentage"]
        at_risk_count = segments_stats["at_risk"]["customer_count"]
        insights = [
            f"The top {pareto_pct:.1f}% of customers account for 80% of total sales, indicating {'high Pareto concentration' if pareto_pct <= 25.0 else 'moderate distribution value'}.",
            f"Champions segment represents {champions_pct:.1f}% of revenue. Prioritize rewarding loyalty in this core category.",
            f"At Risk segment has {at_risk_count} customers. Implement proactive retention campaigns to re-engage before churn.",
            f"Repeat buyers drive {repeat_rate:.1f}% of accounts, contributing {repeat_revenue_share:.1f}% of total sales volume."
        ]

        return {
            "eligible": True,
            "customer_column": cust_col,
            "revenue_column": rev_col,
            "total_customers": total_customers,
            "total_revenue": total_revenue,
            "repeat_count": repeat_count,
            "repeat_rate": round(repeat_rate, 1),
            "repeat_revenue_share": round(repeat_revenue_share, 1),
            "pareto_80_20_customer_pct": round(pareto_pct, 1),
            "pareto_10_concentration": round(concentration_10, 1),
            "pareto_20_concentration": round(concentration_20, 1),
            "segments": segments_stats,
            "top_customers": top_list,
            "insights": insights
        }
    except Exception as e:
        logger.error(f"Customer Intelligence computation failed: {e}", exc_info=True)
        return {
            "eligible": False,
            "message": f"Diagnostics failed during group aggregation: {str(e)}"
        }
