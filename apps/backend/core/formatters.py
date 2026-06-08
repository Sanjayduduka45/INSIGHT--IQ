"""
InsightIQ — Backend Value Formatting Utility

Standardizes currency, percentages, and compact numbers.
Handles numpy types gracefully.
"""

from typing import Any, Union
import numpy as np

def format_currency_python(val: Any, currency: str = "INR") -> str:
    """Formats a numeric value into a compact currency format.
    
    INR: Lakhs / Crores (e.g. ₹4.06 Cr, ₹40.57 L)
    USD: Millions / Billions (e.g. $40.61M, $2.31B)
    """
    try:
        # Convert numpy types to python native types
        if isinstance(val, (np.integer, np.floating)):
            val = val.item()
        
        # Ensure we have a valid float/int
        if val is None:
            return "₹0.00" if currency == "INR" else "$0.00"
            
        f_val = float(val)
        if np.isnan(f_val) or np.isinf(f_val):
            return "0.00"
            
        abs_val = abs(f_val)
        
        if currency == "INR":
            sign = "-" if f_val < 0 else ""
            if abs_val >= 10_000_000:
                return f"{sign}₹{abs_val / 10_000_000:.2f} Cr"
            elif abs_val >= 100_000:
                return f"{sign}₹{abs_val / 100_000:.2f} L"
            elif abs_val >= 1_000:
                return f"{sign}₹{abs_val / 1_000:.2f} K"
            else:
                return f"{sign}₹{abs_val:.2f}"
        else:
            sign = "-" if f_val < 0 else ""
            if abs_val >= 1_000_000_000:
                return f"{sign}${abs_val / 1_000_000_000:.2f}B"
            elif abs_val >= 1_000_000:
                return f"{sign}${abs_val / 1_000_000:.2f}M"
            elif abs_val >= 1_000:
                return f"{sign}${abs_val / 1_000:.2f}K"
            else:
                return f"{sign}${abs_val:.2f}"
    except Exception:
        return str(val)

def format_percent_python(val: Any, is_fraction: bool = None) -> str:
    """Formats a percentage value. If absolute value is <= 1.0, treats as a fraction and multiplies by 100."""
    try:
        if isinstance(val, (np.integer, np.floating)):
            val = val.item()
            
        if val is None:
            return "0.00%"
            
        f_val = float(val)
        if np.isnan(f_val) or np.isinf(f_val):
            return "0.00%"
            
        # Auto-detect if it's a raw fraction or already multiplied
        use_mult = is_fraction if is_fraction is not None else (abs(f_val) <= 1.0)
        num = f_val * 100.0 if use_mult else f_val
        return f"{num:.2f}%"
    except Exception:
        return str(val)

def format_compact_number_python(val: Any, currency: str = None) -> str:
    """Formats a number in compact form. If currency is set, formats as currency."""
    if currency:
        return format_currency_python(val, currency)
    try:
        if isinstance(val, (np.integer, np.floating)):
            val = val.item()
            
        if val is None:
            return "0"
            
        f_val = float(val)
        if np.isnan(f_val) or np.isinf(f_val):
            return "0"
            
        abs_val = abs(f_val)
        sign = "-" if f_val < 0 else ""
        
        # Default compact layout (Millions/Billions)
        if abs_val >= 1_000_000_000:
            return f"{sign}{abs_val / 1_000_000_000:.2f}B"
        elif abs_val >= 1_000_000:
            return f"{sign}{abs_val / 1_000_000:.2f}M"
        elif abs_val >= 1_000:
            return f"{sign}{abs_val / 1_000:.2f}K"
        else:
            if abs_val.is_integer():
                return f"{sign}{int(abs_val)}"
            return f"{sign}{abs_val:.2f}"
    except Exception:
        return str(val)
