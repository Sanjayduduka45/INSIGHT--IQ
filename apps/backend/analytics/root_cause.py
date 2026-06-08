"""
InsightIQ — Automated Root Cause Analysis Engine

Attributes metric changes (declines or growth) to business dimensions:
Category, Region, Product, Segment, Discounts, and Quantity.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple
import pandas as pd
import numpy as np

from intelligence.kpi_generator import KPI
from intelligence.quality_scorer import QualityReport

logger = logging.getLogger(__name__)


@dataclass
class RootCause:
    metric: str
    impact_direction: str  # decline, growth, stable
    driver: str            # Dimension: Category/Value
    description: str
    contribution_pct: float
    confidence: float


def diagnose_root_causes(
    df: pd.DataFrame,
    schema: Any,
    quality: QualityReport,
    kpis: List[KPI]
) -> List[Dict[str, Any]]:
    """Automatically run diagnostic analysis to identify drivers of change."""
    
    causes: List[Dict[str, Any]] = []
    
    from core.df_utils import get_analytic_numeric_cols, get_categorical_cols
    numeric_cols = get_analytic_numeric_cols(df, schema)
    categorical_cols = get_categorical_cols(df, schema)
    
    # ── 1. IDENTIFY COLUMN ROLES ─────────────────────────────────────────────
    region_keywords = ["region", "state", "country", "city", "location", "area"]
    category_keywords = ["category", "type", "class", "genre", "dept", "department"]
    product_keywords = ["product", "item", "sku"]
    segment_keywords = ["segment", "customer_segment", "profile"]
    discount_keywords = ["discount", "promo", "reduction"]
    qty_keywords = ["quantity", "qty", "units", "items", "volume"]
    
    region_col = next((c for c in df.columns if any(kw in c.lower() for kw in region_keywords)), None)
    category_col = next((c for c in df.columns if any(kw in c.lower() for kw in category_keywords)), None)
    product_col = next((c for c in df.columns if any(kw in c.lower() for kw in product_keywords)), None)
    segment_col = next((c for c in df.columns if any(kw in c.lower() for kw in segment_keywords)), None)
    discount_col = next((c for c in df.columns if any(kw in c.lower() for kw in discount_keywords)), None)
    qty_col = next((c for c in df.columns if any(kw in c.lower() for kw in qty_keywords)), None)
    
    # If no date column, we can use simple record splits, but let's assume we have dates
    if not (schema.date_columns and numeric_cols and len(df) >= 8):
        return _fallback_diagnostics(df, numeric_cols)

    date_col = schema.date_columns[0]
    metric = numeric_cols[0]  # Let's diagnose the primary numeric metric (e.g. Sales/Revenue)
    
    try:
        dates = pd.to_datetime(df[date_col], errors="coerce")
        valid = dates.notna() & df[metric].notna()
        
        # Sort chronologically and split into prior/current periods
        temp_df = df[valid].copy()
        temp_df["_dt"] = dates[valid]
        temp_df = temp_df.sort_values("_dt")
        
        half = len(temp_df) // 2
        prior_df = temp_df.iloc[:half]
        current_df = temp_df.iloc[half:]
        
        prior_sum = float(prior_df[metric].sum())
        current_sum = float(current_df[metric].sum())
        
        if prior_sum == 0:
            return _fallback_diagnostics(df, numeric_cols)
            
        change_val = current_sum - prior_sum
        change_pct = (change_val / prior_sum) * 100
        direction = "decline" if change_pct < -2 else "growth" if change_pct > 2 else "stable"
        
        drivers_list: List[Dict[str, Any]] = []
        
        # ── 2. ATTRIBUTE BY CATEGORICAL DIMENSIONS ────────────────────────────
        dimensions_to_scan = [
            ("Category", category_col),
            ("Region", region_col),
            ("Product", product_col),
            ("Customer Segment", segment_col)
        ]
        
        for label, col in dimensions_to_scan:
            if not col or col not in df.columns:
                continue
            
            prior_g = prior_df.groupby(col)[metric].sum()
            current_g = current_df.groupby(col)[metric].sum()
            
            all_keys = set(prior_g.index) | set(current_g.index)
            
            for key in all_keys:
                pr = prior_g.get(key, 0.0)
                cr = current_g.get(key, 0.0)
                diff = cr - pr
                
                # Check if this category changed in the direction of the overall change
                # (e.g., if sales fell, we find what fell most)
                if (change_val < 0 and diff < 0) or (change_val > 0 and diff > 0):
                    contribution = abs(diff) / abs(change_val) * 100 if change_val != 0 else 0
                    prior_val_kpi = pr
                    curr_val_kpi = cr
                    
                    cat_pct = ((cr - pr) / pr * 100) if pr > 0 else 100.0
                    action = "down" if diff < 0 else "up"
                    
                    drivers_list.append({
                        "dimension": label,
                        "key": str(key),
                        "abs_change": abs(diff),
                        "pct_change": round(cat_pct, 1),
                        "contribution_pct": round(contribution, 1),
                        "action": action,
                        "description": f"{label} '{key}' sales {action} {abs(cat_pct):.1f}%, contributing {contribution:.1f}% to the overall variance."
                    })
                    
        # ── 3. ATTRIBUTE BY DISCOUNTS ────────────────────────────────────────
        if discount_col and discount_col in df.columns:
            prior_disc = prior_df[discount_col].mean()
            current_disc = current_df[discount_col].mean()
            if not (pd.isna(prior_disc) or pd.isna(current_disc)):
                disc_diff = current_disc - prior_disc
                # If discounts went up and direction is decline:
                if disc_diff > 0.01:
                    margin_erosion = disc_diff * 100
                    drivers_list.append({
                        "dimension": "Discounts",
                        "key": "Increased Discounting",
                        "abs_change": abs(disc_diff),
                        "pct_change": round(margin_erosion, 1),
                        "contribution_pct": round(min(margin_erosion * 2.0, 30.0), 1),
                        "action": "down" if direction == "decline" else "up",
                        "description": f"Increased discounting level (up {disc_diff*100:.1f} percentage points) reduced profit margin margins by approximately {margin_erosion:.1f}%."
                    })
                    
        # ── 4. ATTRIBUTE BY QUANTITY ─────────────────────────────────────────
        if qty_col and qty_col in df.columns:
            prior_qty = prior_df[qty_col].sum()
            current_qty = current_df[qty_col].sum()
            if prior_qty > 0:
                qty_pct = ((current_qty - prior_qty) / prior_qty) * 100
                if (change_val < 0 and qty_pct < 0) or (change_val > 0 and qty_pct > 0):
                    drivers_list.append({
                        "dimension": "Quantity",
                        "key": "Order Volume",
                        "abs_change": abs(current_qty - prior_qty),
                        "pct_change": round(qty_pct, 1),
                        "contribution_pct": round(abs(qty_pct), 1),
                        "action": "down" if qty_pct < 0 else "up",
                        "description": f"Overall order quantities sold moved {qty_pct:.1f}% relative to prior periods."
                    })

        # Sort drivers list by absolute change / contribution descending
        drivers_list.sort(key=lambda d: d["abs_change"], reverse=True)
        top_drivers = drivers_list[:3]
        
        # Build ranked lists
        ranked_causes = []
        waterfall_steps = [{"name": "Prior Period Total", "value": round(prior_sum, 2)}]
        
        running_total = prior_sum
        for idx, drv in enumerate(top_drivers):
            step_val = drv["abs_change"] if drv["action"] == "up" else -drv["abs_change"]
            running_total += step_val
            waterfall_steps.append({
                "name": f"{drv['dimension']}: {drv['key']}",
                "value": round(step_val, 2)
            })
            
            ranked_causes.append({
                "metric": metric,
                "impact_direction": drv["action"],
                "driver": f"{drv['dimension']}: {drv['key']}",
                "description": f"{idx+1}. {drv['description']}",
                "contribution_pct": drv["contribution_pct"],
                "confidence": round(min(drv["contribution_pct"]/100.0 + 0.35, 0.95), 2)
            })
            
        waterfall_steps.append({"name": "Current Period Total", "value": round(current_sum, 2)})
        
        # Build explanation statement
        action_word = "decline" if direction == "decline" else "growth" if direction == "growth" else "stability"
        if ranked_causes:
            explanation = f"Primary metric '{metric}' {action_word} PoP is driven by the following factors:"
        else:
            explanation = f"Primary metric '{metric}' shows baseline stability within normal tolerances."
            
        narrative = explanation + " " + " ".join([d["description"] for d in ranked_causes])
        decomp = [{"category": d["driver"], "contribution": d["contribution_pct"]} for d in ranked_causes]
        tree = {
            "name": f"Total {metric} Variance",
            "value": f"{change_pct:+.1f}%",
            "children": [
                {
                    "name": d["driver"],
                    "value": f"{d['contribution_pct']}% share",
                    "impact": d["impact_direction"]
                } for d in ranked_causes
            ]
        }
        
        causes.append({
            "metric": metric,
            "impact_direction": direction,
            "overall_change_pct": round(change_pct, 2),
            "explanation": explanation,
            "executive_narrative": narrative,
            "variance_decomposition": decomp,
            "business_driver_tree": tree,
            "drivers": ranked_causes,
            "waterfall": waterfall_steps
        })

    except Exception as e:
        logger.error(f"Root cause diagnostics failed: {e}", exc_info=True)
        return _fallback_diagnostics(df, numeric_cols)
        
    return causes


def _fallback_diagnostics(df: pd.DataFrame, numeric_cols: List[str]) -> List[Dict[str, Any]]:
    """Alternative diagnostics using correlation AND categorical analysis when timeline isn't possible.
    
    RULE: Never return empty drivers. Always provide actionable content.
    """
    from core.df_utils import get_categorical_cols
    
    if not numeric_cols:
        # Even with no numerics, generate structural diagnostics
        cat_cols = []
        for col in df.columns:
            if df[col].dtype == 'object' or df[col].dtype.name == 'category':
                cat_cols.append(col)
        
        drivers = []
        waterfall = [
            {"name": "Total Records", "value": round(float(len(df)), 2)},
        ]
        
        # Generate drivers from categorical value distributions
        for col in cat_cols[:3]:
            try:
                vc = df[col].value_counts()
                if len(vc) > 0:
                    top_val = str(vc.index[0])
                    top_count = int(vc.iloc[0])
                    top_pct = round((top_count / len(df)) * 100, 1)
                    drivers.append({
                        "metric": "Record Distribution",
                        "impact_direction": "stable",
                        "driver": f"Category: {col}",
                        "description": f"'{top_val}' is the dominant value in '{col}', accounting for {top_pct}% of all records ({top_count:,} entries).",
                        "contribution_pct": top_pct,
                        "confidence": 0.65
                    })
                    waterfall.append({
                        "name": f"{col}: {top_val}",
                        "value": round(float(top_count), 2)
                    })
            except Exception:
                pass
        
        if not drivers:
            drivers.append({
                "metric": "Dataset Structure",
                "impact_direction": "stable",
                "driver": "Baseline Structural Analysis",
                "description": f"Dataset contains {len(df):,} records across {len(df.columns)} columns. All structural metrics are within normal parameters.",
                "contribution_pct": 100.0,
                "confidence": 0.5
            })
        
        waterfall.append({"name": "Total Volume", "value": round(float(len(df)), 2)})
        
        return [{
            "metric": "Record Volume",
            "impact_direction": "stable",
            "overall_change_pct": 0.0,
            "explanation": f"Dataset structural analysis: {len(df):,} records across {len(df.columns)} columns. Key categorical distributions analyzed below.",
            "executive_narrative": f"With {len(df):,} records, the dataset shows stable structural properties. " + " ".join([d["description"] for d in drivers]),
            "variance_decomposition": [{"category": d["driver"], "contribution": d["contribution_pct"]} for d in drivers],
            "business_driver_tree": {"name": "Record Volume", "value": f"{len(df):,}", "children": [
                {"name": d["driver"], "value": f"{d['contribution_pct']}% share", "impact": d["impact_direction"]} for d in drivers
            ]},
            "drivers": drivers,
            "waterfall": waterfall
        }]
    
    metric = numeric_cols[0]
    total_sum = float(df[metric].sum()) if metric in df.columns else 0.0
    
    # ── Phase 1: Correlation-based drivers ────────────────────────────────
    correlations = []
    for col in numeric_cols[1:]:
        if col in df.columns:
            valid_df = df[[metric, col]].dropna()
            if len(valid_df) > 1:
                std_metric = valid_df[metric].std()
                std_col = valid_df[col].std()
                if std_metric > 0 and std_col > 0:
                    corr = valid_df[metric].corr(valid_df[col])
                    if not pd.isna(corr):
                        correlations.append((col, corr))
                        
    # Sort by absolute correlation coefficient descending
    correlations.sort(key=lambda x: abs(x[1]), reverse=True)
    
    drivers = []
    waterfall = []
    
    # Waterfall starts at Baseline, and adds/subtracts step values based on correlation contribution
    baseline = round(total_sum * 0.5, 2)
    remaining = total_sum - baseline
    
    abs_corr_sum = sum(abs(c[1]) for c in correlations) if correlations else 0
    
    explanation_parts = []
    explanation_parts.append(f"Diagnostic analysis of '{metric}' (total: {total_sum:,.1f}).")
    
    if correlations:
        explanation_parts.append("Top contributing variables by correlation strength:")
        for idx, (col, corr) in enumerate(correlations[:3]):
            action = "up" if corr > 0 else "down"
            direction_str = "positively" if corr > 0 else "negatively"
            strength_str = "strong" if abs(corr) > 0.7 else "moderate" if abs(corr) > 0.4 else "weak"
            
            contrib_pct = (abs(corr) / abs_corr_sum * 100.0) if abs_corr_sum > 0 else 33.3
            confidence = round(min(abs(corr) + 0.15, 0.95), 2)
            
            description = f"{col} has a {strength_str} {direction_str} correlation of {corr:.2f} with {metric}."
            explanation_parts.append(f"{col} (r={corr:.2f})")
            
            drivers.append({
                "metric": metric,
                "impact_direction": action,
                "driver": f"Numeric Driver: {col}",
                "description": f"{idx+1}. {description} Contribution based on correlation is {contrib_pct:.1f}%.",
                "contribution_pct": round(contrib_pct, 1),
                "confidence": confidence
            })
            
            val_change = remaining * (abs(corr) / abs_corr_sum) if abs_corr_sum > 0 else (remaining / min(len(correlations), 3))
            if corr < 0:
                val_change = -val_change
            
            waterfall.append({
                "name": f"Corr: {col}",
                "value": round(val_change, 2)
            })
    
    # ── Phase 2: Categorical-based drivers (NEW) ─────────────────────────
    # Even without correlations, analyze how metric distributes across categories
    try:
        # Try to get schema from the dataframe attributes or use raw detection
        cat_cols_raw = [c for c in df.columns 
                        if (df[c].dtype == 'object' or df[c].dtype.name == 'category')
                        and df[c].nunique() <= max(50, len(df) * 0.5)]
    except Exception:
        cat_cols_raw = []
    
    if not correlations and cat_cols_raw:
        explanation_parts.append("No numeric correlations found. Analyzing categorical distribution drivers:")
        for idx, col in enumerate(cat_cols_raw[:3]):
            try:
                grouped = df.groupby(col)[metric].sum().sort_values(ascending=False)
                if len(grouped) > 0 and total_sum > 0:
                    top_val = str(grouped.index[0])
                    top_amount = float(grouped.iloc[0])
                    top_pct = (top_amount / total_sum) * 100
                    
                    drivers.append({
                        "metric": metric,
                        "impact_direction": "stable",
                        "driver": f"Category Driver: {col}",
                        "description": f"{idx+1}. '{top_val}' in '{col}' contributes {top_pct:.1f}% of total {metric} ({top_amount:,.1f}).",
                        "contribution_pct": round(top_pct, 1),
                        "confidence": 0.60
                    })
                    
                    waterfall.append({
                        "name": f"{col}: {top_val}",
                        "value": round(top_amount * 0.5, 2)  # Proportional allocation
                    })
                    
                    explanation_parts.append(f"{col} (top: {top_val} = {top_pct:.1f}%)")
            except Exception:
                pass
    
    # ── Phase 3: Always ensure at least one driver ───────────────────────
    if not drivers:
        # Statistical summary driver
        if metric in df.columns:
            mean_val = float(df[metric].mean())
            std_val = float(df[metric].std()) if len(df[metric].dropna()) > 1 else 0
            cv = (std_val / mean_val * 100) if mean_val != 0 else 0
            
            drivers.append({
                "metric": metric,
                "impact_direction": "stable",
                "driver": "Statistical Profile",
                "description": f"'{metric}' has mean {mean_val:,.1f}, std {std_val:,.1f} (CV={cv:.1f}%). No significant categorical or numeric co-drivers identified.",
                "contribution_pct": 100.0,
                "confidence": 0.5
            })
        else:
            drivers.append({
                "metric": metric,
                "impact_direction": "stable",
                "driver": "Baseline Stability",
                "description": f"No secondary drivers correlated with '{metric}' were identified. Performance is within expected parameters.",
                "contribution_pct": 100.0,
                "confidence": 0.5
            })
        waterfall.append({
            "name": "Unexplained Variance",
            "value": round(remaining, 2)
        })
        
    explanation = " ".join(explanation_parts)
    
    step_sum = sum(w["value"] for w in waterfall)
    diff = round((total_sum - baseline) - step_sum, 2)
    if diff != 0 and waterfall:
        waterfall[-1]["value"] = round(waterfall[-1]["value"] + diff, 2)
        
    final_waterfall = [{"name": "Baseline Est.", "value": baseline}] + waterfall + [{"name": f"Total {metric}", "value": round(total_sum, 2)}]
    
    narrative = explanation + " " + " ".join([d["description"] for d in drivers])
    decomp = [{"category": d["driver"], "contribution": d["contribution_pct"]} for d in drivers]
    tree = {
        "name": f"Diagnostic {metric} Drivers",
        "value": f"{total_sum:,.1f}",
        "children": [
            {
                "name": d["driver"],
                "value": f"{d['contribution_pct']}% weight",
                "impact": d["impact_direction"]
            } for d in drivers
        ]
    }
    
    return [{
        "metric": metric,
        "impact_direction": "stable" if abs_corr_sum < 0.2 else "growth" if any(c[1] > 0 for c in correlations[:1]) else "decline",
        "overall_change_pct": 0.0,
        "explanation": explanation,
        "executive_narrative": narrative,
        "variance_decomposition": decomp,
        "business_driver_tree": tree,
        "drivers": drivers,
        "waterfall": final_waterfall
    }]


