import pandas as pd
import sys
from pathlib import Path

# Add apps/backend to sys path
ROOT = Path("/Users/sanjayduduka/Ai Analyst Agent")
sys.path.insert(0, str(ROOT / "apps" / "backend"))

from intelligence.schema_detector import detect_schema
from intelligence.domain_classifier import classify_domain
from analytics.charts import recommend_charts
from analytics.customer_intelligence import compute_customer_intelligence

# Load sample sales dataset
df = pd.read_csv(ROOT / "sample_sales.csv")
schema = detect_schema(df)
domain = classify_domain(df, schema)

print(f"Dataset columns: {list(df.columns)}")
print(f"Detected domain: {domain.domain}")
print(f"Schema date cols: {schema.date_columns}")
print(f"Schema num cols: {schema.numeric_columns}")
print(f"Schema cat cols: {schema.categorical_columns}")

# Test customer eligibility
ci = compute_customer_intelligence(df, schema)
print(f"Customer Intelligence Eligible: {ci.get('eligible')}")
if not ci.get('eligible'):
    print(f"Reason: {ci.get('message')}")

# Test executive
exec_charts = recommend_charts(df, schema, "executive")
print(f"Executive Dashboard Charts Count: {len(exec_charts)}")
for i, c in enumerate(exec_charts):
    print(f"  {i+1}. {c['title']} ({c['type']})")

# Test kpi
kpi_charts = recommend_charts(df, schema, "kpi")
print(f"KPI Dashboard Charts Count: {len(kpi_charts)}")
for i, c in enumerate(kpi_charts):
    print(f"  {i+1}. {c['title']} ({c['type']})")

# Test customer
cust_charts = recommend_charts(df, schema, "customer")
print(f"Customer Dashboard Charts Count: {len(cust_charts)}")
for i, c in enumerate(cust_charts):
    print(f"  {i+1}. {c['title']} ({c['type']})")
