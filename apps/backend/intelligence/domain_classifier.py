"""
InsightIQ — Domain Classifier

Automatically identifies the business domain of a dataset
by analyzing column names, data patterns, and value distributions.

Supported domains:
  Sales, Finance, Healthcare, HR, Education, Manufacturing,
  Logistics, Insurance, Retail, Telecom, Agriculture, IoT,
  Cybersecurity, Energy, Government, Generic
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

import pandas as pd

from intelligence.schema_detector import DatasetSchema

logger = logging.getLogger(__name__)


@dataclass
class DomainResult:
    """Domain classification result."""

    domain: str
    confidence: float
    sub_domain: str = ""
    evidence: List[str] = field(default_factory=list)
    all_scores: Dict[str, float] = field(default_factory=dict)


# ── Domain keyword maps ──────────────────────────────────────────────────

DOMAIN_SIGNATURES: Dict[str, List[str]] = {
    "SaaS": [
        "subscription",
        "mrr",
        "arr",
        "churn",
        "cac",
        "ltv",
        "recurring",
        "user_license",
        "licensing",
        "mau",
        "active_users",
        "upgrade",
        "downgrade",
        "retention",
        "billing",
    ],
    "Sales": [
        "revenue",
        "sales",
        "order",
        "product",
        "customer",
        "discount",
        "quantity",
        "profit",
        "margin",
        "shipment",
        "ship",
        "category",
        "sub_category",
        "segment",
        "region",
        "store",
        "purchase",
        "invoice",
    ],
    "Finance": [
        "transaction",
        "account",
        "balance",
        "credit",
        "debit",
        "interest",
        "loan",
        "deposit",
        "withdrawal",
        "portfolio",
        "stock",
        "ticker",
        "dividend",
        "equity",
        "bond",
        "fund",
        "forex",
        "currency",
        "exchange",
        "investment",
        "asset",
        "liability",
        "fiscal",
        "tax",
        "audit",
    ],
    "Healthcare": [
        "patient",
        "diagnosis",
        "treatment",
        "hospital",
        "doctor",
        "nurse",
        "medication",
        "prescription",
        "symptom",
        "disease",
        "clinical",
        "readmission",
        "discharge",
        "surgery",
        "lab",
        "blood",
        "bmi",
        "insurance_claim",
        "icd",
        "admission",
        "recovery",
        "vital",
    ],
    "HR": [
        "employee",
        "salary",
        "department",
        "hire",
        "attrition",
        "resignation",
        "promotion",
        "performance",
        "attendance",
        "leave",
        "benefits",
        "compensation",
        "engagement",
        "tenure",
        "manager",
        "job_title",
        "satisfaction",
        "training",
        "overtime",
        "workforce",
    ],
    "Education": [
        "student",
        "grade",
        "score",
        "course",
        "enrollment",
        "teacher",
        "attendance",
        "gpa",
        "semester",
        "exam",
        "class",
        "subject",
        "school",
        "university",
        "degree",
        "graduation",
        "dropout",
        "scholarship",
        "curriculum",
        "faculty",
    ],
    "Manufacturing": [
        "production",
        "defect",
        "quality",
        "machine",
        "downtime",
        "yield",
        "batch",
        "assembly",
        "inspection",
        "material",
        "inventory",
        "warehouse",
        "supplier",
        "component",
        "factory",
        "maintenance",
        "oee",
        "scrap",
        "shift",
        "throughput",
    ],
    "Logistics": [
        "shipment",
        "delivery",
        "tracking",
        "route",
        "fleet",
        "warehouse",
        "carrier",
        "freight",
        "logistics",
        "supply_chain",
        "transit",
        "dispatch",
        "container",
        "port",
        "customs",
        "origin",
        "destination",
    ],
    "Insurance": [
        "policy",
        "claim",
        "premium",
        "coverage",
        "insured",
        "beneficiary",
        "underwriting",
        "actuarial",
        "deductible",
        "liability",
        "risk",
        "renewal",
        "lapse",
        "endorsement",
    ],
    "Retail": [
        "sku",
        "upc",
        "shelf",
        "aisle",
        "basket",
        "checkout",
        "loyalty",
        "coupon",
        "promotion",
        "footfall",
        "conversion",
        "merchandise",
        "return",
        "refund",
        "pos",
        "ecommerce",
        "cart",
    ],
    "Marketing": [
        "campaign",
        "click",
        "impression",
        "conversion",
        "lead",
        "cpc",
        "roi",
        "audience",
        "channel",
        "social",
        "engagement",
        "reach",
        "email",
        "open_rate",
        "bounce_rate",
        "funnel",
    ],
    "Customer Analytics": [
        "customer",
        "churn",
        "nps",
        "satisfaction",
        "lifetime_value",
        "clv",
        "retention",
        "segment",
        "behavior",
        "feedback",
        "survey",
        "review",
        "subscription",
        "loyalty",
    ],
    "Traffic & Transportation": [
        "traffic",
        "accident",
        "vehicle",
        "speed",
        "road",
        "collision",
        "injury",
        "fatality",
        "pedestrian",
        "intersection",
        "weather",
        "transit",
        "bus",
        "train",
        "flight",
        "delay",
        "passenger",
    ],
    "Telecom": [
        "subscriber",
        "churn",
        "call",
        "data_usage",
        "roaming",
        "plan",
        "bandwidth",
        "network",
        "signal",
        "tower",
        "arpu",
        "mou",
        "handset",
        "prepaid",
        "postpaid",
        "sms",
    ],
    "Agriculture": [
        "crop",
        "yield",
        "harvest",
        "soil",
        "rainfall",
        "irrigation",
        "fertilizer",
        "pesticide",
        "farm",
        "acreage",
        "livestock",
        "seed",
        "season",
        "planting",
    ],
    "IoT": [
        "sensor",
        "device",
        "telemetry",
        "reading",
        "temperature",
        "humidity",
        "pressure",
        "voltage",
        "firmware",
        "gateway",
        "actuator",
        "mqtt",
        "iot",
        "edge",
    ],
    "Cybersecurity": [
        "threat",
        "vulnerability",
        "incident",
        "malware",
        "firewall",
        "intrusion",
        "alert",
        "attack",
        "phishing",
        "encryption",
        "authentication",
        "breach",
        "log",
        "ip_address",
        "packet",
    ],
    "Energy": [
        "consumption",
        "generation",
        "kwh",
        "megawatt",
        "solar",
        "wind",
        "grid",
        "utility",
        "meter",
        "tariff",
        "emission",
        "carbon",
        "renewable",
        "fossil",
        "turbine",
    ],
    "Census": [
        "population",
        "census",
        "demographics",
        "age",
        "gender",
        "race",
        "ethnicity",
        "income",
        "household",
        "education",
        "employment",
        "occupancy",
        "citizenship",
        "birthplace",
        "marital_status",
    ],
    "Operations": [
        "uptime",
        "utilization",
        "throughput",
        "cycle_time",
        "lead_time",
        "backlog",
        "capacity",
        "bottleneck",
        "process",
        "efficiency",
        "downtime",
        "oee",
        "schedule",
        "resource",
    ],
}


def classify_domain(df: pd.DataFrame, schema: DatasetSchema) -> DomainResult:
    """Classify the dataset's business domain."""
    # Normalize all column names for matching
    col_tokens = set()
    for col in df.columns:
        normalized = col.lower().replace(" ", "_").replace("-", "_")
        col_tokens.add(normalized)
        # Also add individual tokens
        for token in normalized.split("_"):
            if len(token) > 2:
                col_tokens.add(token)

    # Score each domain
    scores: Dict[str, float] = {}
    evidence_map: Dict[str, List[str]] = {}

    for domain, keywords in DOMAIN_SIGNATURES.items():
        matches = []
        for kw in keywords:
            for token in col_tokens:
                if kw in token or token in kw:
                    matches.append(kw)
                    break

        score = len(matches) / max(len(keywords), 1)
        scores[domain] = round(score, 4)
        evidence_map[domain] = matches[:5]  # Top 5 evidence terms

    # Also consider value-based signals
    _boost_from_values(df, scores)

    # Pick the best domain
    if not scores:
        return DomainResult(domain="Generic", confidence=0.0)

    best_domain = max(scores, key=scores.get)  # type: ignore[arg-type]
    best_score = scores[best_domain]

    # Calculate final confidence scaled up, capped at 0.99
    # If a domain has 15-20% of its keywords matched, it should be highly confident.
    final_confidence = round(min(best_score * 4.0, 0.99), 2)

    # If confidence is below 70%, fall back to Generic strictly
    if final_confidence < 0.70:
        return DomainResult(
            domain="Generic",
            confidence=final_confidence,
            evidence=["Not enough strong signals for a specific domain. Defaulting to Generic."],
            all_scores=scores,
        )

    return DomainResult(
        domain=best_domain,
        confidence=final_confidence,
        evidence=evidence_map.get(best_domain, []),
        all_scores=scores,
    )


def _boost_from_values(df: pd.DataFrame, scores: Dict[str, float]) -> None:
    """Boost domain scores based on actual data values."""
    # Check for currency-formatted values (Sales/Finance)
    for col in df.select_dtypes(include=["object"]).columns[:5]:
        sample = df[col].dropna().head(50).astype(str)
        if sample.str.startswith("$").mean() > 0.3:
            scores["Sales"] = scores.get("Sales", 0) + 0.1
            scores["Finance"] = scores.get("Finance", 0) + 0.05

    # Check for medical codes (Healthcare)
    for col in df.columns:
        cl = col.lower()
        if "icd" in cl or "cpt" in cl or "drg" in cl:
            scores["Healthcare"] = scores.get("Healthcare", 0) + 0.2

    # Check for IP addresses (Cybersecurity/IoT)
    for col in df.select_dtypes(include=["object"]).columns[:5]:
        sample = df[col].dropna().head(20).astype(str)
        if sample.str.match(r"\d+\.\d+\.\d+\.\d+").mean() > 0.3:
            scores["Cybersecurity"] = scores.get("Cybersecurity", 0) + 0.15
            scores["IoT"] = scores.get("IoT", 0) + 0.1
