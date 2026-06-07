# Design Document

## Overview

The AI Data Analyst Agent is a multi-agent AI system that provides automated data analysis capabilities for business datasets. The system follows a modular, agent-based architecture where specialized agents collaborate to perform complex analysis tasks including KPI calculation, anomaly detection, root cause analysis, and business recommendations.

This design document specifies the technical architecture, component design, data flows, API specifications, and correctness properties for the MVP implementation targeting hackathon demonstration with local deployment.

## System Architecture

### High-Level Architecture

The system follows a three-tier architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend Layer                          │
│  (React Application - localhost:3000)                       │
│  - File Upload Interface                                    │
│  - Dashboard Views (Dataset, KPI, Anomaly)                  │
│  - Chat Interface                                           │
│  - Executive Report View                                    │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP REST API
                         │
┌────────────────────────▼────────────────────────────────────┐
│                     Backend Layer                           │
│  (FastAPI Application - localhost:8000)                     │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         AI Data Analyst Agent (Orchestrator)        │   │
│  │  - Request routing                                  │   │
│  │  - Agent coordination                               │   │
│  │  - Context passing                                  │   │
│  │  - Error handling                                  │   │
│  └────────────┬────────────────────────────────────────┘   │
│               │                                             │
│  ┌────────────▼─────────────────────────────────────────┐  │
│  │           Specialized Agent Layer                    │  │
│  │                                                       │  │
│  │  ┌──────────────┐  ┌──────────────┐                 │  │
│  │  │ Understanding│  │   Analysis   │                 │  │
│  │  │    Agent     │  │    Agent     │                 │  │
│  │  └──────────────┘  └──────────────┘                 │  │
│  │                                                       │  │
│  │  ┌──────────────┐  ┌──────────────┐                 │  │
│  │  │   Anomaly    │  │Recommendation│                 │  │
│  │  │   Detection  │  │    Agent     │                 │  │
│  │  │    Agent     │  │              │                 │  │
│  │  └──────────────┘  └──────────────┘                 │  │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │            Data & Storage Layer                     │   │
│  │  - In-Memory Dataset Store                          │   │
│  │  - Analysis Results Cache                           │   │
│  │  - Request Queue                                    │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ HTTPS API Calls
                         │
┌────────────────────────▼────────────────────────────────────┐
│              External Services Layer                        │
│  Azure OpenAI Service (GPT-4)                               │
│  - Natural language understanding                           │
│  - Business insight generation                              │
│  - Recommendation reasoning                                 │
└─────────────────────────────────────────────────────────────┘
```

### Multi-Agent Architecture Pattern


The system implements a **hierarchical multi-agent architecture** with one orchestrator and four specialized agents:

**Orchestrator Pattern:**
- **AI Data Analyst Agent** acts as the central orchestrator
- Routes requests to appropriate specialized agents based on task type
- Manages agent execution sequence for multi-step workflows
- Aggregates results from multiple agents
- Handles error recovery and partial result compilation

**Specialized Agent Pattern:**
Each specialized agent follows a consistent interface:
```python
class BaseAgent:
    def analyze(self, dataset: DataFrame, context: dict) -> dict:
        """Execute agent-specific analysis"""
        pass
    
    def validate_input(self, dataset: DataFrame) -> bool:
        """Validate inputs before processing"""
        pass
```

**Agent Responsibilities:**

1. **Understanding Agent**: Dataset schema and quality analysis
   - Column detection and type inference
   - Missing value analysis
   - Data quality metrics

2. **Analysis Agent**: KPI calculation and statistical analysis
   - KPI computation (revenue, profit, churn, growth, retention)
   - Trend analysis
   - Root cause identification through correlation analysis

3. **Anomaly Detection Agent**: Outlier identification
   - Statistical anomaly detection (z-score, IQR)
   - Categorical frequency analysis
   - Temporal anomaly detection

4. **Recommendation Agent**: Business insight generation
   - Recommendation synthesis from analysis results
   - Business impact prioritization
   - Actionable insight generation


## Component Design

### 1. Frontend Components

#### Technology Stack
- **Framework**: React 18.x
- **State Management**: React Context API + Hooks
- **HTTP Client**: Axios
- **UI Components**: Material-UI (MUI)
- **Charts**: Recharts or Chart.js
- **Styling**: CSS Modules with MUI theming

#### Component Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── FileUpload/
│   │   │   ├── FileUpload.jsx
│   │   │   ├── FileUpload.module.css
│   │   │   └── FileUpload.test.jsx
│   │   ├── Dashboard/
│   │   │   ├── DatasetOverview.jsx
│   │   │   ├── KPIAnalysisDashboard.jsx
│   │   │   ├── AnomalyDetectionView.jsx
│   │   │   └── Dashboard.module.css
│   │   ├── Chat/
│   │   │   ├── ChatInterface.jsx
│   │   │   ├── ChatMessage.jsx
│   │   │   └── Chat.module.css
│   │   ├── Report/
│   │   │   ├── ExecutiveReport.jsx
│   │   │   └── Report.module.css
│   │   └── Common/
│   │       ├── LoadingIndicator.jsx
│   │       ├── ErrorMessage.jsx
│   │       └── Header.jsx
│   ├── services/
│   │   └── api.js
│   ├── context/
│   │   └── DataContext.jsx
│   ├── App.jsx
│   └── index.js
├── public/
└── package.json
```


#### Key Component Designs

**FileUpload Component**
```javascript
// FileUpload.jsx
const FileUpload = () => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);

  const handleUpload = async (event) => {
    const selectedFile = event.target.files[0];
    
    // Validate file type
    const validTypes = ['.csv', '.xlsx', '.xls'];
    const fileExt = selectedFile.name.substring(selectedFile.name.lastIndexOf('.'));
    
    if (!validTypes.includes(fileExt)) {
      setError('Invalid file type. Please upload CSV or Excel files.');
      return;
    }
    
    // Validate file size (50MB limit)
    if (selectedFile.size > 50 * 1024 * 1024) {
      setError('File size exceeds 50MB limit.');
      return;
    }
    
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      
      const response = await api.uploadDataset(formData);
      setFile(response.data);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    // JSX with upload button, progress indicator, error display
  );
};
```


**DatasetOverview Component**
```javascript
// DatasetOverview.jsx
const DatasetOverview = ({ datasetId }) => {
  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchOverview = async () => {
      try {
        const response = await api.getDatasetUnderstanding(datasetId);
        setOverview(response.data);
      } catch (err) {
        // Error handling
      } finally {
        setLoading(false);
      }
    };
    fetchOverview();
  }, [datasetId]);

  if (loading) return <LoadingIndicator />;

  return (
    <div>
      <h2>Dataset Overview</h2>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Column</TableCell>
            <TableCell>Data Type</TableCell>
            <TableCell>Missing %</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {overview.columns.map(col => (
            <TableRow key={col.name}>
              <TableCell>{col.name}</TableCell>
              <TableCell>{col.dataType}</TableCell>
              <TableCell>{col.missingPercentage}%</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
};
```


**ChatInterface Component**
```javascript
// ChatInterface.jsx
const ChatInterface = ({ datasetId }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [waiting, setWaiting] = useState(false);

  const sendMessage = async () => {
    if (!input.trim()) return;
    
    const userMessage = { role: 'user', content: input };
    setMessages([...messages, userMessage]);
    setInput('');
    setWaiting(true);
    
    try {
      const response = await api.askQuestion(datasetId, input);
      const aiMessage = { role: 'assistant', content: response.data.answer };
      setMessages(prev => [...prev, aiMessage]);
    } catch (err) {
      // Error handling
    } finally {
      setWaiting(false);
    }
  };

  return (
    <div className="chat-container">
      <div className="message-list">
        {messages.map((msg, idx) => (
          <ChatMessage key={idx} message={msg} />
        ))}
        {waiting && <LoadingIndicator />}
      </div>
      <div className="input-area">
        <input value={input} onChange={e => setInput(e.target.value)} />
        <button onClick={sendMessage}>Send</button>
      </div>
    </div>
  );
};
```

### 2. Backend Components

#### Technology Stack
- **Framework**: FastAPI 0.100+
- **Python Version**: 3.9+
- **Data Processing**: Pandas 2.0+, NumPy 1.24+
- **Statistical Analysis**: SciPy 1.10+, scikit-learn 1.3+
- **Azure OpenAI**: openai 1.0+, azure-identity 1.14+
- **HTTP Client**: httpx 0.24+
- **Validation**: Pydantic 2.0+


#### Backend Structure

```
backend/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── dataset.py
│   │   │   ├── analysis.py
│   │   │   ├── chat.py
│   │   │   └── report.py
│   │   └── dependencies.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py
│   │   ├── orchestrator.py
│   │   ├── understanding_agent.py
│   │   ├── analysis_agent.py
│   │   ├── anomaly_detection_agent.py
│   │   └── recommendation_agent.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── azure_openai_service.py
│   │   ├── dataset_service.py
│   │   └── storage_service.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── dataset.py
│   │   ├── analysis.py
│   │   └── response.py
│   └── utils/
│       ├── __init__.py
│       ├── logger.py
│       └── validators.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── property/
├── data/
│   └── demo_datasets/
├── requirements.txt
└── .env.example
```


#### Core Agent Implementations

**Base Agent Interface**
```python
# agents/base_agent.py
from abc import ABC, abstractmethod
from typing import Dict, Any
import pandas as pd

class BaseAgent(ABC):
    """Base class for all specialized agents"""
    
    def __init__(self, azure_openai_service):
        self.azure_openai_service = azure_openai_service
        self.logger = get_logger(self.__class__.__name__)
    
    @abstractmethod
    async def analyze(self, dataset: pd.DataFrame, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent-specific analysis"""
        pass
    
    @abstractmethod
    def validate_input(self, dataset: pd.DataFrame) -> bool:
        """Validate inputs before processing"""
        pass
    
    def handle_error(self, error: Exception) -> Dict[str, Any]:
        """Standardized error handling"""
        self.logger.error(f"Error in {self.__class__.__name__}: {str(error)}")
        return {
            "status": "error",
            "agent": self.__class__.__name__,
            "error_message": str(error)
        }
```

**Understanding Agent**
```python
# agents/understanding_agent.py
class UnderstandingAgent(BaseAgent):
    """Agent responsible for dataset schema detection and data quality assessment"""
    
    async def analyze(self, dataset: pd.DataFrame, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze dataset structure and quality"""
        
        if not self.validate_input(dataset):
            raise ValueError("Invalid dataset for understanding analysis")
        
        columns_info = []
        
        for col in dataset.columns:
            col_info = {
                "name": col,
                "dataType": self._infer_type(dataset[col]),
                "missingCount": dataset[col].isna().sum(),
                "missingPercentage": (dataset[col].isna().sum() / len(dataset)) * 100,
                "category": self._categorize_column(dataset[col])
            }
            columns_info.append(col_info)
        
        return {
            "status": "success",
            "columns": columns_info,
            "rowCount": len(dataset),
            "columnCount": len(dataset.columns)
        }
    
    def _infer_type(self, series: pd.Series) -> str:
        """Infer data type of a column"""
        if pd.api.types.is_numeric_dtype(series):
            return "numeric"
        elif pd.api.types.is_datetime64_any_dtype(series):
            return "datetime"
        else:
            return "categorical"
    
    def _categorize_column(self, series: pd.Series) -> str:
        """Categorize column as numeric, categorical, or datetime"""
        if pd.api.types.is_numeric_dtype(series):
            return "numeric"
        elif pd.api.types.is_datetime64_any_dtype(series):
            return "datetime"
        else:
            # Check if should be treated as categorical
            unique_ratio = series.nunique() / len(series)
            return "categorical" if unique_ratio < 0.5 else "text"
    
    def validate_input(self, dataset: pd.DataFrame) -> bool:
        """Validate dataset is not empty"""
        return dataset is not None and not dataset.empty
```

**Analysis Agent**
```python
# agents/analysis_agent.py
class AnalysisAgent(BaseAgent):
    """Agent responsible for KPI calculation and root cause analysis"""
    
    async def analyze(self, dataset: pd.DataFrame, context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform KPI analysis and root cause identification"""
        
        analysis_type = context.get("analysis_type", "kpi")
        
        if analysis_type == "kpi":
            return await self._calculate_kpis(dataset, context)
        elif analysis_type == "root_cause":
            return await self._analyze_root_cause(dataset, context)
        else:
            raise ValueError(f"Unknown analysis type: {analysis_type}")
    
    async def _calculate_kpis(self, dataset: pd.DataFrame, context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate KPIs based on available columns"""
        
        # Use Azure OpenAI to identify relevant columns
        column_mapping = await self._identify_kpi_columns(dataset.columns.tolist())
        
        kpis = {}
        
        # Revenue KPIs
        if column_mapping.get("revenue"):
            revenue_col = column_mapping["revenue"]
            kpis["total_revenue"] = dataset[revenue_col].sum()
            
            if column_mapping.get("date"):
                date_col = column_mapping["date"]
                kpis["revenue_trend"] = self._calculate_trend(dataset, revenue_col, date_col)
        
        # Profit KPIs
        if column_mapping.get("profit"):
            profit_col = column_mapping["profit"]
            kpis["total_profit"] = dataset[profit_col].sum()
            
            if column_mapping.get("revenue"):
                revenue_col = column_mapping["revenue"]
                kpis["profit_margin"] = (dataset[profit_col].sum() / dataset[revenue_col].sum()) * 100
        
        # Customer KPIs
        if column_mapping.get("churn"):
            churn_col = column_mapping["churn"]
            kpis["churn_rate"] = (dataset[churn_col].sum() / len(dataset)) * 100
        
        if column_mapping.get("customer_id") and column_mapping.get("date"):
            kpis["customer_growth_rate"] = self._calculate_growth_rate(
                dataset, column_mapping["customer_id"], column_mapping["date"]
            )
        
        return {"status": "success", "kpis": kpis}
    
    async def _analyze_root_cause(self, dataset: pd.DataFrame, context: Dict[str, Any]) -> Dict[str, Any]:
        """Identify root causes for KPI changes"""
        
        target_kpi = context.get("target_kpi")
        if not target_kpi or target_kpi not in dataset.columns:
            raise ValueError(f"Target KPI {target_kpi} not found in dataset")
        
        # Calculate correlations with numeric columns
        numeric_cols = dataset.select_dtypes(include=['number']).columns
        correlations = []
        
        for col in numeric_cols:
            if col != target_kpi:
                corr = dataset[target_kpi].corr(dataset[col])
                correlations.append({
                    "variable": col,
                    "correlation": corr,
                    "abs_correlation": abs(corr)
                })
        
        # Sort by absolute correlation strength
        correlations.sort(key=lambda x: x["abs_correlation"], reverse=True)
        
        # Analyze categorical distributions
        categorical_cols = dataset.select_dtypes(include=['object']).columns
        categorical_analysis = []
        
        for col in categorical_cols:
            grouped = dataset.groupby(col)[target_kpi].mean()
            categorical_analysis.append({
                "variable": col,
                "distribution": grouped.to_dict()
            })
        
        # Generate natural language explanation using Azure OpenAI
        explanation = await self._generate_root_cause_explanation(
            target_kpi, correlations[:5], categorical_analysis
        )
        
        return {
            "status": "success",
            "target_kpi": target_kpi,
            "correlations": correlations[:10],
            "categorical_analysis": categorical_analysis,
            "explanation": explanation
        }
    
    async def _identify_kpi_columns(self, columns: list) -> Dict[str, str]:
        """Use Azure OpenAI to map column names to KPI types"""
        
        prompt = f"""Given these dataset columns: {columns}
        
Identify which columns correspond to:
- revenue
- profit
- date/time
- customer_id
- churn (binary indicator)

Return a JSON mapping of KPI type to column name."""
        
        response = await self.azure_openai_service.complete(
            prompt=prompt,
            system_message="You are a data analyst identifying KPI columns."
        )
        
        return response  # Parsed JSON response
    
    def validate_input(self, dataset: pd.DataFrame) -> bool:
        """Validate dataset has sufficient data for analysis"""
        return dataset is not None and not dataset.empty and len(dataset) > 1
```

**Anomaly Detection Agent**
```python
# agents/anomaly_detection_agent.py
from scipy import stats
import numpy as np

class AnomalyDetectionAgent(BaseAgent):
    """Agent responsible for identifying outliers and anomalies"""
    
    async def analyze(self, dataset: pd.DataFrame, context: Dict[str, Any]) -> Dict[str, Any]:
        """Detect anomalies in dataset"""
        
        anomalies = []
        
        # Detect numeric anomalies using z-score and IQR
        numeric_cols = dataset.select_dtypes(include=['number']).columns
        for col in numeric_cols:
            col_anomalies = self._detect_numeric_anomalies(dataset, col)
            anomalies.extend(col_anomalies)
        
        # Detect categorical anomalies using frequency analysis
        categorical_cols = dataset.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            col_anomalies = self._detect_categorical_anomalies(dataset, col)
            anomalies.extend(col_anomalies)
        
        # Calculate anomaly scores
        for anomaly in anomalies:
            anomaly["score"] = self._calculate_anomaly_score(anomaly)
        
        # Sort by score and take top 20
        anomalies.sort(key=lambda x: x["score"], reverse=True)
        top_anomalies = anomalies[:20]
        
        # Generate explanations for top anomalies using Azure OpenAI
        for anomaly in top_anomalies:
            anomaly["explanation"] = await self._generate_anomaly_explanation(anomaly, dataset)
        
        return {
            "status": "success",
            "anomalies": top_anomalies,
            "total_detected": len(anomalies)
        }
    
    def _detect_numeric_anomalies(self, dataset: pd.DataFrame, column: str) -> list:
        """Detect outliers in numeric column using z-score and IQR methods"""
        
        anomalies = []
        series = dataset[column].dropna()
        
        # Z-score method
        z_scores = np.abs(stats.zscore(series))
        z_outliers = np.where(z_scores > 3)[0]
        
        # IQR method
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        iqr_outliers = series[(series < lower_bound) | (series > upper_bound)].index
        
        # Combine results
        outlier_indices = set(series.index[z_outliers]) | set(iqr_outliers)
        
        for idx in outlier_indices:
            anomalies.append({
                "row_index": idx,
                "column": column,
                "value": dataset.loc[idx, column],
                "type": "numeric_outlier",
                "z_score": z_scores[series.index.get_loc(idx)] if idx in z_outliers else None
            })
        
        return anomalies
    
    def _detect_categorical_anomalies(self, dataset: pd.DataFrame, column: str) -> list:
        """Detect rare categories in categorical column"""
        
        anomalies = []
        value_counts = dataset[column].value_counts()
        total_count = len(dataset)
        
        # Consider categories appearing in < 1% of records as anomalies
        rare_threshold = 0.01
        
        for value, count in value_counts.items():
            frequency = count / total_count
            if frequency < rare_threshold:
                # Find rows with this rare value
                rare_indices = dataset[dataset[column] == value].index
                for idx in rare_indices:
                    anomalies.append({
                        "row_index": idx,
                        "column": column,
                        "value": value,
                        "type": "rare_category",
                        "frequency": frequency
                    })
        
        return anomalies
    
    def _calculate_anomaly_score(self, anomaly: dict) -> float:
        """Calculate anomaly score based on type and metrics"""
        
        if anomaly["type"] == "numeric_outlier":
            # Higher z-score = higher anomaly score
            return anomaly.get("z_score", 3.0)
        elif anomaly["type"] == "rare_category":
            # Lower frequency = higher anomaly score
            return 1.0 / (anomaly["frequency"] + 0.001)
        else:
            return 1.0
    
    def validate_input(self, dataset: pd.DataFrame) -> bool:
        """Validate dataset has sufficient data for anomaly detection"""
        return dataset is not None and not dataset.empty and len(dataset) > 10
```


**Recommendation Agent**
```python
# agents/recommendation_agent.py
class RecommendationAgent(BaseAgent):
    """Agent responsible for generating actionable business recommendations"""
    
    async def analyze(self, dataset: pd.DataFrame, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate business recommendations from analysis results"""
        
        # Extract analysis results from context
        kpi_results = context.get("kpi_results", {})
        root_cause_results = context.get("root_cause_results", {})
        anomaly_results = context.get("anomaly_results", {})
        
        # Generate recommendations using Azure OpenAI
        recommendations = await self._generate_recommendations(
            kpi_results, root_cause_results, anomaly_results
        )
        
        # Prioritize by business impact
        prioritized = self._prioritize_recommendations(recommendations)
        
        return {
            "status": "success",
            "recommendations": prioritized
        }
    
    async def _generate_recommendations(self, kpis: dict, root_causes: dict, anomalies: dict) -> list:
        """Use Azure OpenAI to generate actionable recommendations"""
        
        prompt = f"""Based on the following business analysis:

KPIs: {kpis}
Root Causes: {root_causes}
Anomalies: {anomalies}

Generate at least 3 actionable business recommendations. For each recommendation:
1. State the action clearly
2. Explain the reasoning based on the data
3. Estimate potential business impact (high/medium/low)

Format as JSON array of recommendations."""
        
        response = await self.azure_openai_service.complete(
            prompt=prompt,
            system_message="You are a business analyst providing data-driven recommendations."
        )
        
        return response  # Parsed JSON array
    
    def _prioritize_recommendations(self, recommendations: list) -> list:
        """Sort recommendations by business impact"""
        
        impact_priority = {"high": 3, "medium": 2, "low": 1}
        
        for rec in recommendations:
            rec["impact_score"] = impact_priority.get(rec.get("impact", "low"), 1)
        
        recommendations.sort(key=lambda x: x["impact_score"], reverse=True)
        return recommendations
    
    def validate_input(self, dataset: pd.DataFrame) -> bool:
        """Recommendation agent doesn't directly validate dataset"""
        return True
```

**Orchestrator Agent**
```python
# agents/orchestrator.py
class OrchestratorAgent:
    """Main orchestrator that coordinates specialized agents"""
    
    def __init__(self, understanding_agent, analysis_agent, anomaly_agent, recommendation_agent):
        self.understanding_agent = understanding_agent
        self.analysis_agent = analysis_agent
        self.anomaly_agent = anomaly_agent
        self.recommendation_agent = recommendation_agent
        self.logger = get_logger("OrchestratorAgent")
    
    async def process_request(self, request_type: str, dataset: pd.DataFrame, context: Dict[str, Any]) -> Dict[str, Any]:
        """Route request to appropriate agent(s)"""
        
        try:
            if request_type == "understand":
                return await self.understanding_agent.analyze(dataset, context)
            
            elif request_type == "analyze_kpi":
                return await self.analysis_agent.analyze(dataset, {"analysis_type": "kpi"})
            
            elif request_type == "root_cause":
                return await self.analysis_agent.analyze(dataset, {"analysis_type": "root_cause", **context})
            
            elif request_type == "detect_anomalies":
                return await self.anomaly_agent.analyze(dataset, context)
            
            elif request_type == "generate_recommendations":
                return await self.recommendation_agent.analyze(dataset, context)
            
            elif request_type == "executive_report":
                return await self._generate_executive_report(dataset, context)
            
            elif request_type == "conversational_query":
                return await self._handle_conversational_query(dataset, context)
            
            else:
                raise ValueError(f"Unknown request type: {request_type}")
        
        except Exception as e:
            self.logger.error(f"Error processing request {request_type}: {str(e)}")
            return {
                "status": "error",
                "request_type": request_type,
                "error": str(e)
            }
    
    async def _generate_executive_report(self, dataset: pd.DataFrame, context: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate multiple agents to generate comprehensive executive report"""
        
        results = {}
        
        # Run analysis in sequence, passing context between agents
        try:
            # Step 1: KPI Analysis
            kpi_results = await self.analysis_agent.analyze(dataset, {"analysis_type": "kpi"})
            results["kpis"] = kpi_results.get("kpis", {})
            
            # Step 2: Anomaly Detection
            anomaly_results = await self.anomaly_agent.analyze(dataset, {})
            results["top_anomalies"] = anomaly_results.get("anomalies", [])[:5]
            
            # Step 3: Root Cause Analysis (if target KPI specified)
            if context.get("target_kpi"):
                root_cause_results = await self.analysis_agent.analyze(
                    dataset, 
                    {"analysis_type": "root_cause", "target_kpi": context["target_kpi"]}
                )
                results["top_root_causes"] = root_cause_results.get("correlations", [])[:3]
            
            # Step 4: Generate Recommendations
            recommendation_context = {
                "kpi_results": results.get("kpis", {}),
                "root_cause_results": results.get("top_root_causes", []),
                "anomaly_results": results.get("top_anomalies", [])
            }
            recommendation_results = await self.recommendation_agent.analyze(dataset, recommendation_context)
            results["top_recommendations"] = recommendation_results.get("recommendations", [])[:5]
            
            return {
                "status": "success",
                "executive_report": results
            }
        
        except Exception as e:
            # Return partial results with error information
            results["status"] = "partial"
            results["error"] = str(e)
            return results
    
    async def _handle_conversational_query(self, dataset: pd.DataFrame, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle natural language queries by routing to appropriate agent"""
        
        query = context.get("query", "")
        
        # Determine query intent and route to appropriate agent
        # This would use Azure OpenAI to classify the query intent
        intent = await self._classify_query_intent(query)
        
        if intent == "kpi":
            return await self.analysis_agent.analyze(dataset, {"analysis_type": "kpi"})
        elif intent == "anomaly":
            return await self.anomaly_agent.analyze(dataset, {})
        elif intent == "data_retrieval":
            # Handle simple data queries directly
            return self._query_data(dataset, query)
        else:
            # Default: use Azure OpenAI to answer
            return await self._answer_with_openai(dataset, query)
```


### 3. Azure OpenAI Service Integration

**Service Implementation**
```python
# services/azure_openai_service.py
from openai import AzureOpenAI
import asyncio
from typing import Optional

class AzureOpenAIService:
    """Service for interacting with Azure OpenAI GPT-4"""
    
    def __init__(self, api_key: str, endpoint: str, api_version: str = "2024-02-15-preview"):
        self.client = AzureOpenAI(
            api_key=api_key,
            azure_endpoint=endpoint,
            api_version=api_version
        )
        self.model = "gpt-4"
        self.max_retries = 3
        self.logger = get_logger("AzureOpenAIService")
    
    async def complete(
        self, 
        prompt: str, 
        system_message: str = "You are a helpful AI assistant.",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> dict:
        """Complete a prompt with retry logic and exponential backoff"""
        
        for attempt in range(self.max_retries):
            try:
                response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                content = response.choices[0].message.content
                
                # Try to parse as JSON if content looks like JSON
                if content.strip().startswith('{') or content.strip().startswith('['):
                    import json
                    return json.loads(content)
                
                return {"response": content}
            
            except Exception as e:
                self.logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < self.max_retries - 1:
                    # Exponential backoff: 1s, 2s, 4s
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error(f"All {self.max_retries} attempts failed")
                    raise Exception(f"Azure OpenAI service unavailable after {self.max_retries} retries")
```

### 4. Storage Service

**In-Memory Storage Implementation**
```python
# services/storage_service.py
from typing import Dict, Optional
import pandas as pd
import uuid

class InMemoryStorageService:
    """In-memory storage for datasets and analysis results"""
    
    def __init__(self):
        self.datasets: Dict[str, pd.DataFrame] = {}
        self.analysis_cache: Dict[str, dict] = {}
        self.request_queue: list = []
        self.logger = get_logger("StorageService")
    
    def store_dataset(self, dataset: pd.DataFrame) -> str:
        """Store dataset and return unique ID"""
        dataset_id = str(uuid.uuid4())
        self.datasets[dataset_id] = dataset
        self.logger.info(f"Stored dataset {dataset_id} with {len(dataset)} rows")
        return dataset_id
    
    def get_dataset(self, dataset_id: str) -> Optional[pd.DataFrame]:
        """Retrieve dataset by ID"""
        return self.datasets.get(dataset_id)
    
    def delete_dataset(self, dataset_id: str) -> bool:
        """Delete dataset from memory"""
        if dataset_id in self.datasets:
            del self.datasets[dataset_id]
            self.logger.info(f"Deleted dataset {dataset_id}")
            return True
        return False
    
    def cache_analysis(self, key: str, result: dict) -> None:
        """Cache analysis result"""
        self.analysis_cache[key] = result
    
    def get_cached_analysis(self, key: str) -> Optional[dict]:
        """Get cached analysis result"""
        return self.analysis_cache.get(key)
    
    def clear_all(self) -> None:
        """Clear all stored data (called on application restart)"""
        self.datasets.clear()
        self.analysis_cache.clear()
        self.request_queue.clear()
        self.logger.info("Cleared all stored data")
    
    def enqueue_request(self, request: dict) -> None:
        """Add request to processing queue"""
        self.request_queue.append(request)
    
    def dequeue_request(self) -> Optional[dict]:
        """Get next request from queue"""
        if self.request_queue:
            return self.request_queue.pop(0)
        return None
```

## Data Flow Diagrams

### 1. Dataset Upload Flow

```
User Browser                Frontend                Backend API              Storage Service
     |                          |                         |                         |
     |---Upload CSV/Excel------>|                         |                         |
     |                          |                         |                         |
     |                          |--Validate File Type---->|                         |
     |                          |                         |                         |
     |                          |                         |--Validate Size--------->|
     |                          |                         |                         |
     |                          |                         |--Parse File------------>|
     |                          |                         |                         |
     |                          |                         |--Store Dataset--------->|
     |                          |                         |<--Dataset ID------------|
     |                          |<--Success Response------|                         |
     |<--Show Dataset ID--------|                         |                         |
```


### 2. Dataset Understanding Flow

```
Frontend            Backend API         Orchestrator        Understanding Agent      Azure OpenAI
   |                     |                    |                      |                     |
   |--GET /understand--->|                    |                      |                     |
   |                     |                    |                      |                     |
   |                     |--Route Request---->|                      |                     |
   |                     |                    |                      |                     |
   |                     |                    |--Analyze Dataset---->|                     |
   |                     |                    |                      |                     |
   |                     |                    |                      |--Detect Columns--->|
   |                     |                    |                      |--Infer Types------>|
   |                     |                    |                      |--Calculate Missing>|
   |                     |                    |                      |                     |
   |                     |                    |<--Results------------|                     |
   |                     |<--Response---------|                      |                     |
   |<--Display Overview--|                    |                      |                     |
```

### 3. KPI Analysis Flow

```
Frontend        Backend API      Orchestrator     Analysis Agent    Azure OpenAI
   |                 |                 |                  |                |
   |--GET /kpi------>|                 |                  |                |
   |                 |                 |                  |                |
   |                 |--Route--------->|                  |                |
   |                 |                 |                  |                |
   |                 |                 |--Analyze KPI---->|                |
   |                 |                 |                  |                |
   |                 |                 |                  |--Identify----->|
   |                 |                 |                  |   Columns      |
   |                 |                 |                  |<--Mapping------|
   |                 |                 |                  |                |
   |                 |                 |                  |--Calculate-----|
   |                 |                 |                  |   KPIs         |
   |                 |                 |                  |                |
   |                 |                 |<--KPI Results----|                |
   |                 |<--Response------|                  |                |
   |<--Display KPIs--|                 |                  |                |
```


### 4. Executive Report Generation Flow (Multi-Agent Coordination)

```
Frontend    Backend API   Orchestrator   Analysis   Anomaly    Recommendation   Azure OpenAI
   |             |              |          Agent     Agent         Agent             |
   |--GET        |              |            |         |             |               |
   | /report---->|              |            |         |             |               |
   |             |              |            |         |             |               |
   |             |--Route------>|            |         |             |               |
   |             |              |            |         |             |               |
   |             |              |--Step 1:-->|         |             |               |
   |             |              |  KPI       |         |             |               |
   |             |              |<--Results--|         |             |               |
   |             |              |            |         |             |               |
   |             |              |--Step 2:---------->|             |               |
   |             |              |  Anomalies         |             |               |
   |             |              |<--Results----------|             |               |
   |             |              |            |         |             |               |
   |             |              |--Step 3:-->|         |             |               |
   |             |              | Root Cause |         |             |               |
   |             |              |<--Results--|         |             |               |
   |             |              |            |         |             |               |
   |             |              |--Step 4:---------------------->|               |
   |             |              | Recommendations                |               |
   |             |              |                                |--Generate----->|
   |             |              |                                |<--Insights-----|
   |             |              |<--Results----------------------|               |
   |             |              |            |         |             |               |
   |             |              |--Compile Report      |             |               |
   |             |<--Report-----|            |         |             |               |
   |<--Display---|              |            |         |             |               |
```


## API Endpoint Specifications

### Base Configuration
- **Base URL**: `http://localhost:8000/api/v1`
- **Content-Type**: `application/json`
- **Request Timeout**: 30 seconds

### Endpoints

#### 1. Dataset Management

**POST /datasets/upload**

Upload a new dataset file.

Request:
```
POST /api/v1/datasets/upload
Content-Type: multipart/form-data

file: <CSV or Excel file>
```

Response (Success):
```json
{
  "status": "success",
  "datasetId": "uuid-string",
  "rowCount": 1000,
  "columnCount": 15,
  "message": "Dataset uploaded successfully"
}
```

Response (Error):
```json
{
  "status": "error",
  "message": "Invalid file format. Only CSV and Excel files are supported.",
  "code": "INVALID_FILE_FORMAT"
}
```

**GET /datasets/{datasetId}**

Retrieve dataset metadata.

Response:
```json
{
  "datasetId": "uuid-string",
  "rowCount": 1000,
  "columnCount": 15,
  "uploadedAt": "2024-01-15T10:30:00Z"
}
```

**DELETE /datasets/{datasetId}**

Delete a dataset from memory.

Response:
```json
{
  "status": "success",
  "message": "Dataset deleted successfully"
}
```


#### 2. Dataset Understanding

**GET /analysis/{datasetId}/understand**

Get dataset schema and quality analysis.

Response:
```json
{
  "status": "success",
  "datasetId": "uuid-string",
  "columns": [
    {
      "name": "revenue",
      "dataType": "numeric",
      "missingCount": 5,
      "missingPercentage": 0.5,
      "category": "numeric"
    },
    {
      "name": "product_category",
      "dataType": "categorical",
      "missingCount": 0,
      "missingPercentage": 0,
      "category": "categorical"
    }
  ],
  "rowCount": 1000,
  "columnCount": 15,
  "processingTime": 2.3
}
```

#### 3. KPI Analysis

**GET /analysis/{datasetId}/kpi**

Calculate key performance indicators.

Response:
```json
{
  "status": "success",
  "datasetId": "uuid-string",
  "kpis": {
    "total_revenue": 1500000.50,
    "revenue_trend": {
      "direction": "increasing",
      "percentage_change": 12.5
    },
    "total_profit": 450000.25,
    "profit_margin": 30.0,
    "churn_rate": 5.2,
    "customer_growth_rate": 8.3,
    "retention_rate": 94.8
  },
  "processingTime": 8.7
}
```


#### 4. Root Cause Analysis

**POST /analysis/{datasetId}/root-cause**

Identify factors influencing KPI changes.

Request:
```json
{
  "targetKpi": "revenue"
}
```

Response:
```json
{
  "status": "success",
  "datasetId": "uuid-string",
  "targetKpi": "revenue",
  "correlations": [
    {
      "variable": "marketing_spend",
      "correlation": 0.85,
      "abs_correlation": 0.85
    },
    {
      "variable": "customer_satisfaction",
      "correlation": 0.72,
      "abs_correlation": 0.72
    }
  ],
  "categoricalAnalysis": [
    {
      "variable": "region",
      "distribution": {
        "North": 500000,
        "South": 450000,
        "East": 350000,
        "West": 200000
      }
    }
  ],
  "explanation": "Revenue is strongly correlated with marketing spend (0.85) and customer satisfaction (0.72). Regional analysis shows North region generates highest revenue.",
  "processingTime": 12.1
}
```

#### 5. Anomaly Detection

**GET /analysis/{datasetId}/anomalies**

Detect outliers and unusual patterns.

Response:
```json
{
  "status": "success",
  "datasetId": "uuid-string",
  "anomalies": [
    {
      "rowIndex": 543,
      "column": "transaction_amount",
      "value": 99999.99,
      "type": "numeric_outlier",
      "score": 5.2,
      "explanation": "This transaction amount is 5.2 standard deviations above the mean, suggesting a potentially unusual large transaction."
    }
  ],
  "totalDetected": 47,
  "processingTime": 13.5
}
```


#### 6. Recommendations

**GET /analysis/{datasetId}/recommendations**

Get business recommendations based on analysis.

Optional Query Parameters:
- `kpiResults`: JSON string of KPI analysis results
- `rootCauseResults`: JSON string of root cause findings
- `anomalyResults`: JSON string of anomaly detection results

Response:
```json
{
  "status": "success",
  "datasetId": "uuid-string",
  "recommendations": [
    {
      "action": "Increase marketing spend in North region by 15%",
      "reasoning": "North region shows highest revenue correlation with marketing spend (0.85) and currently underinvested compared to potential.",
      "impact": "high",
      "impactScore": 3
    },
    {
      "action": "Investigate unusual large transactions in Q4",
      "reasoning": "5 anomalous transactions detected with values >5 standard deviations, requiring fraud review.",
      "impact": "high",
      "impactScore": 3
    },
    {
      "action": "Implement customer retention program in South region",
      "reasoning": "South region shows 8% higher churn rate than average, with potential for 5% revenue recovery.",
      "impact": "medium",
      "impactScore": 2
    }
  ],
  "processingTime": 9.2
}
```

#### 7. Conversational Analytics

**POST /chat/{datasetId}/ask**

Ask natural language questions about the dataset.

Request:
```json
{
  "question": "What is the average revenue by product category?"
}
```


Response:
```json
{
  "status": "success",
  "datasetId": "uuid-string",
  "question": "What is the average revenue by product category?",
  "answer": "The average revenue by product category is: Electronics: $1,250, Clothing: $850, Home & Garden: $620, Sports: $540.",
  "visualization": {
    "type": "bar",
    "data": {
      "Electronics": 1250,
      "Clothing": 850,
      "Home & Garden": 620,
      "Sports": 540
    }
  },
  "processingTime": 6.8
}
```

#### 8. Executive Report

**GET /analysis/{datasetId}/report**

Generate comprehensive executive report.

Optional Query Parameters:
- `targetKpi`: KPI column name for root cause analysis

Response:
```json
{
  "status": "success",
  "datasetId": "uuid-string",
  "executiveReport": {
    "kpis": {
      "total_revenue": 1500000.50,
      "profit_margin": 30.0,
      "churn_rate": 5.2
    },
    "topRootCauses": [
      {
        "variable": "marketing_spend",
        "correlation": 0.85
      },
      {
        "variable": "customer_satisfaction",
        "correlation": 0.72
      }
    ],
    "topAnomalies": [
      {
        "rowIndex": 543,
        "column": "transaction_amount",
        "score": 5.2
      }
    ],
    "topRecommendations": [
      {
        "action": "Increase marketing spend in North region by 15%",
        "impact": "high"
      }
    ]
  },
  "processingTime": 18.5
}
```


## Database and Storage Design

### In-Memory Storage Architecture

For the MVP, all data is stored in memory using Python dictionaries and Pandas DataFrames. This approach provides:
- Fast read/write access
- Simple implementation
- Automatic cleanup on restart
- No external database dependencies

### Storage Models

**1. Dataset Storage**
```python
# Data structure
datasets: Dict[str, pd.DataFrame] = {}

# Example entry
{
  "uuid-123": <DataFrame with 1000 rows × 15 columns>
}
```

**2. Analysis Cache Storage**
```python
# Data structure
analysis_cache: Dict[str, dict] = {}

# Example entry
{
  "uuid-123:kpi": {
    "timestamp": "2024-01-15T10:30:00Z",
    "result": {...},
    "ttl": 300  # Cache for 5 minutes
  }
}
```

**3. Request Queue**
```python
# Data structure
request_queue: List[dict] = []

# Example entry
{
  "requestId": "req-456",
  "datasetId": "uuid-123",
  "type": "kpi_analysis",
  "timestamp": "2024-01-15T10:30:00Z",
  "status": "pending"
}
```

### Data Lifecycle

1. **Upload**: Dataset parsed from CSV/Excel → stored as DataFrame with UUID
2. **Analysis**: Results computed and cached with dataset ID + analysis type as key
3. **Retrieval**: Cached results returned if available and not expired
4. **Cleanup**: All data cleared on application restart


### Memory Management

**Dataset Size Limits**:
- Maximum 100,000 rows per dataset
- Maximum 50 columns per dataset
- Maximum 50MB file upload size

**Memory Estimation**:
- Typical dataset (10,000 rows × 15 columns): ~5-10 MB
- Maximum dataset (100,000 rows × 50 columns): ~200-400 MB
- Analysis cache: ~1-5 MB per analysis
- Total estimated memory usage: < 500 MB

## Complete Folder Structure

```
ai-data-analyst-agent/
├── README.md
├── .gitignore
├── .env.example
├── docker-compose.yml (optional)
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI application entry point
│   │   ├── config.py                  # Configuration and environment variables
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── routes/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── dataset.py         # Dataset upload/management endpoints
│   │   │   │   ├── analysis.py        # Analysis endpoints (understand, KPI, root cause, anomaly)
│   │   │   │   ├── chat.py            # Conversational analytics endpoints
│   │   │   │   └── report.py          # Executive report endpoint
│   │   │   └── dependencies.py        # FastAPI dependencies
│   │   │
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── base_agent.py          # Abstract base agent class
│   │   │   ├── orchestrator.py        # Main orchestrator agent
│   │   │   ├── understanding_agent.py  # Schema detection & data quality
│   │   │   ├── analysis_agent.py      # KPI calculation & root cause
│   │   │   ├── anomaly_detection_agent.py  # Outlier detection
│   │   │   └── recommendation_agent.py     # Business recommendations
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── azure_openai_service.py    # Azure OpenAI integration
│   │   │   ├── dataset_service.py         # Dataset parsing and validation
│   │   │   └── storage_service.py         # In-memory storage management
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── dataset.py             # Pydantic models for datasets
│   │   │   ├── analysis.py            # Pydantic models for analysis results
│   │   │   └── response.py            # Pydantic models for API responses
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── logger.py              # Logging configuration
│   │       └── validators.py          # Input validation utilities
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── unit/
│   │   │   ├── test_understanding_agent.py
│   │   │   ├── test_analysis_agent.py
│   │   │   ├── test_anomaly_agent.py
│   │   │   └── test_recommendation_agent.py
│   │   ├── integration/
│   │   │   ├── test_api_endpoints.py
│   │   │   └── test_multi_agent_flow.py
│   │   └── property/
│   │       └── test_analysis_properties.py
│   │
│   ├── data/
│   │   └── demo_datasets/
│   │       ├── sales_data.csv
│   │       ├── customer_churn.csv
│   │       └── financial_metrics.xlsx
│   │
│   ├── requirements.txt
│   └── run.py                         # Backend startup script
│
├── frontend/
│   ├── public/
│   │   ├── index.html
│   │   └── favicon.ico
│   │
│   ├── src/
│   │   ├── components/
│   │   │   ├── FileUpload/
│   │   │   │   ├── FileUpload.jsx
│   │   │   │   ├── FileUpload.module.css
│   │   │   │   └── FileUpload.test.jsx
│   │   │   │
│   │   │   ├── Dashboard/
│   │   │   │   ├── DatasetOverview.jsx
│   │   │   │   ├── KPIAnalysisDashboard.jsx
│   │   │   │   ├── AnomalyDetectionView.jsx
│   │   │   │   └── Dashboard.module.css
│   │   │   │
│   │   │   ├── Chat/
│   │   │   │   ├── ChatInterface.jsx
│   │   │   │   ├── ChatMessage.jsx
│   │   │   │   └── Chat.module.css
│   │   │   │
│   │   │   ├── Report/
│   │   │   │   ├── ExecutiveReport.jsx
│   │   │   │   └── Report.module.css
│   │   │   │
│   │   │   └── Common/
│   │   │       ├── LoadingIndicator.jsx
│   │   │       ├── ErrorMessage.jsx
│   │   │       ├── Header.jsx
│   │   │       └── Common.module.css
│   │   │
│   │   ├── services/
│   │   │   └── api.js                 # API client with axios
│   │   │
│   │   ├── context/
│   │   │   └── DataContext.jsx        # React Context for state management
│   │   │
│   │   ├── App.jsx                    # Main application component
│   │   ├── App.css
│   │   └── index.js                   # React entry point
│   │
│   ├── package.json
│   ├── package-lock.json
│   └── .env.example
│
└── docs/
    ├── setup.md                       # Setup instructions
    ├── api_documentation.md           # API reference
    └── architecture.md                # Architecture details
```


## Technology Stack Details

### Backend Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Framework | FastAPI | 0.100+ | REST API framework with async support |
| Language | Python | 3.9+ | Core programming language |
| Data Processing | Pandas | 2.0+ | DataFrame operations and analysis |
| Numerical Computing | NumPy | 1.24+ | Numerical array operations |
| Statistical Analysis | SciPy | 1.10+ | Statistical methods and correlations |
| Machine Learning | scikit-learn | 1.3+ | Anomaly detection algorithms |
| AI Integration | openai | 1.0+ | Azure OpenAI SDK |
| Authentication | azure-identity | 1.14+ | Azure authentication |
| HTTP Client | httpx | 0.24+ | Async HTTP requests |
| Validation | Pydantic | 2.0+ | Data validation and settings |
| File Parsing | openpyxl | 3.1+ | Excel file parsing |
| ASGI Server | uvicorn | 0.23+ | Production ASGI server |

### Frontend Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Framework | React | 18.x | UI component framework |
| Build Tool | Vite | 4.x | Fast build tool and dev server |
| UI Library | Material-UI (MUI) | 5.x | Component library |
| HTTP Client | Axios | 1.5+ | API communication |
| Charts | Recharts | 2.8+ | Data visualization |
| State Management | React Context + Hooks | Built-in | Application state |
| Styling | CSS Modules + MUI | - | Component styling |

### Development Tools

| Tool | Purpose |
|------|---------|
| pytest | Unit and integration testing |
| pytest-asyncio | Async test support |
| hypothesis | Property-based testing |
| black | Code formatting |
| flake8 | Linting |
| mypy | Type checking |
| ESLint | JavaScript linting |
| Prettier | Code formatting |


## Azure OpenAI Integration Patterns

### Authentication Pattern

```python
# Using API Key Authentication
from openai import AzureOpenAI

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version="2024-02-15-preview"
)
```

### Retry Pattern with Exponential Backoff

```python
async def complete_with_retry(prompt: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            response = await client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ]
            )
            return response
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                await asyncio.sleep(wait_time)
            else:
                raise Exception(f"Service unavailable after {max_retries} retries")
```

### Rate Limiting Pattern

```python
from asyncio import Semaphore

class RateLimiter:
    def __init__(self, max_concurrent: int = 5):
        self.semaphore = Semaphore(max_concurrent)
    
    async def execute(self, func, *args, **kwargs):
        async with self.semaphore:
            return await func(*args, **kwargs)
```

### Structured Output Pattern

```python
# System prompts guide structured responses
system_message = """You are a data analyst. Always respond in valid JSON format.
For KPI identification, return: {"revenue": "column_name", "profit": "column_name"}
For recommendations, return: [{"action": "...", "reasoning": "...", "impact": "high|medium|low"}]
"""

# Parse JSON responses
response = await client.chat.completions.create(...)
content = response.choices[0].message.content
parsed_result = json.loads(content)
```


### Agent-Specific Prompt Patterns

**Understanding Agent Prompts:**
```python
# Not required for Understanding Agent - uses pandas introspection
# No Azure OpenAI calls needed for schema detection
```

**Analysis Agent Prompts:**
```python
# Column identification prompt
column_prompt = f"""Given these dataset columns: {columns}

Identify which columns correspond to:
- revenue (sales, income, or revenue metrics)
- profit (net profit, gross profit)
- date/time (temporal data)
- customer_id (unique customer identifier)
- churn (binary indicator of customer leaving)

Return JSON mapping: {{"revenue": "column_name", ...}}
Only include mappings for columns that exist."""

# Root cause explanation prompt
explanation_prompt = f"""Target KPI: {kpi_name}

Top correlations:
{correlations}

Categorical analysis:
{categorical_data}

Provide a business-focused explanation of the key factors driving changes in this KPI.
Focus on actionable insights. Keep response under 200 words."""
```

**Anomaly Detection Agent Prompts:**
```python
# Anomaly explanation prompt
anomaly_prompt = f"""Detected anomaly:
Row: {row_index}
Column: {column_name}
Value: {value}
Type: {anomaly_type}
Score: {score}

Surrounding context:
{context_rows}

Explain why this record is anomalous and what it might indicate.
Keep response concise (2-3 sentences)."""
```

**Recommendation Agent Prompts:**
```python
# Recommendation generation prompt
recommendation_prompt = f"""Based on this business analysis:

KPIs:
{json.dumps(kpis, indent=2)}

Root Causes:
{json.dumps(root_causes, indent=2)}

Anomalies:
{json.dumps(anomalies, indent=2)}

Generate 3-5 actionable business recommendations. For each:
1. State the action clearly
2. Explain reasoning based on the data
3. Estimate potential business impact (high/medium/low)

Return JSON array:
[
  {{
    "action": "specific action to take",
    "reasoning": "data-driven explanation",
    "impact": "high|medium|low"
  }}
]"""
```


## Error Handling Patterns

### Agent Error Handling

```python
class BaseAgent:
    def handle_error(self, error: Exception) -> Dict[str, Any]:
        """Standardized error handling across all agents"""
        self.logger.error(f"Error in {self.__class__.__name__}: {str(error)}")
        return {
            "status": "error",
            "agent": self.__class__.__name__,
            "error_message": str(error),
            "error_type": type(error).__name__
        }
```

### API Error Responses

```python
# FastAPI exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={
            "status": "error",
            "message": str(exc),
            "code": "VALIDATION_ERROR"
        }
    )

@app.exception_handler(FileNotFoundError)
async def not_found_handler(request: Request, exc: FileNotFoundError):
    return JSONResponse(
        status_code=404,
        content={
            "status": "error",
            "message": "Dataset not found",
            "code": "DATASET_NOT_FOUND"
        }
    )
```

### Partial Results Pattern

```python
# Orchestrator returns partial results when some agents fail
async def _generate_executive_report(self, dataset, context):
    results = {"status": "partial", "errors": []}
    
    try:
        results["kpis"] = await self.analysis_agent.analyze(...)
    except Exception as e:
        results["errors"].append({"agent": "analysis", "error": str(e)})
    
    try:
        results["anomalies"] = await self.anomaly_agent.analyze(...)
    except Exception as e:
        results["errors"].append({"agent": "anomaly", "error": str(e)})
    
    if not results["errors"]:
        results["status"] = "success"
    
    return results
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: File Format Validation

*For any* file uploaded to the system, the Backend_API SHALL accept the file if and only if it has a valid CSV (.csv) or Excel (.xlsx, .xls) extension

**Validates: Requirements 1.1, 1.2, 1.3**

### Property 2: File Upload Error Messaging

*For any* invalid file upload attempt, the Backend_API SHALL return a non-empty error message describing the specific validation failure

**Validates: Requirements 1.4**

### Property 3: Dataset Storage Round-Trip

*For any* valid dataset uploaded to the system, retrieving the dataset by its ID SHALL return a dataset with the same content and structure

**Validates: Requirements 1.5**

### Property 4: Column Detection Completeness

*For any* valid dataset, the Understanding_Agent SHALL detect all column names without omission or duplication

**Validates: Requirements 2.1**

### Property 5: Data Type Inference Consistency

*For any* dataset with columns of known data types (numeric, categorical, datetime), the Understanding_Agent SHALL correctly identify the data type category for each column

**Validates: Requirements 2.2, 2.5, 2.6, 2.7**

### Property 6: Missing Value Count Accuracy

*For any* dataset, the count of missing values per column SHALL equal the actual number of null/NaN values in that column

**Validates: Requirements 2.3**

### Property 7: Missing Value Percentage Relationship

*For any* dataset and column, the missing value percentage SHALL equal (missing_count / total_rows) * 100

**Validates: Requirements 2.4**


### Property 8: Revenue KPI Calculation

*For any* dataset with a revenue column, the calculated total revenue SHALL equal the sum of all revenue values in that column

**Validates: Requirements 3.1**

### Property 9: Profit Margin Relationship

*For any* dataset with profit and revenue columns, the calculated profit margin SHALL equal (total_profit / total_revenue) * 100

**Validates: Requirements 3.4**

### Property 10: Churn Rate Calculation

*For any* dataset with a churn indicator column, the calculated churn rate SHALL equal (sum_of_churn_indicators / total_rows) * 100

**Validates: Requirements 3.5**

### Property 11: Correlation Coefficient Ranking

*For any* set of correlation coefficients produced by root cause analysis, the ranking of influencing factors SHALL be ordered by descending absolute correlation value

**Validates: Requirements 4.5**

### Property 12: Anomaly Score Assignment

*For any* detected anomaly, the anomaly SHALL have a non-null anomaly score value assigned

**Validates: Requirements 5.2**

### Property 13: Top Anomalies Ranking

*For any* set of detected anomalies, the top 20 returned anomalies SHALL be ordered by descending anomaly score

**Validates: Requirements 5.7**

### Property 14: Recommendation Count Minimum

*For any* complete analysis with KPI, root cause, and anomaly results, the Recommendation_Agent SHALL generate at least 3 recommendations

**Validates: Requirements 6.6**


### Property 15: Recommendation Reasoning Presence

*For any* generated recommendation, the recommendation SHALL include non-empty reasoning text

**Validates: Requirements 6.7**

### Property 16: Recommendation Prioritization Order

*For any* set of recommendations with business impact scores, the recommendations SHALL be ordered by descending impact score (high=3, medium=2, low=1)

**Validates: Requirements 6.5**

### Property 17: Query Routing Correctness

*For any* natural language question containing KPI-related keywords (revenue, profit, churn, growth), the AI_Data_Analyst_Agent SHALL route the query to the Analysis_Agent

**Validates: Requirements 7.3**

### Property 18: Data Retrieval Correctness

*For any* data retrieval query targeting stored dataset content, the returned data SHALL match the actual values present in the in-memory dataset

**Validates: Requirements 7.4**

### Property 19: Chart Configuration Validity

*For any* visualization query response, the returned chart configuration SHALL contain valid chart type and data structure

**Validates: Requirements 7.6**

### Property 20: Executive Report Completeness

*For any* executive report generation request with complete agent results, the report SHALL include KPI values, anomalies, and recommendations from all agents

**Validates: Requirements 8.1**

### Property 21: Executive Report Top 3 Root Causes

*For any* root cause analysis with results, the executive report SHALL include exactly the top 3 root causes ranked by correlation strength

**Validates: Requirements 8.4**


### Property 22: Executive Report Top 5 Anomalies

*For any* anomaly detection with results, the executive report SHALL include exactly the top 5 anomalies ranked by anomaly score

**Validates: Requirements 8.5**

### Property 23: Executive Report Top 5 Recommendations

*For any* recommendation generation with results, the executive report SHALL include exactly the top 5 recommendations

**Validates: Requirements 8.6**

### Property 24: In-Memory Storage Verification

*For any* dataset storage operation, the dataset SHALL be retrievable from memory and SHALL NOT result in any disk write operations

**Validates: Requirements 9.3**

### Property 25: Agent Orchestration Routing

*For any* request of type "understand", "analyze_kpi", "root_cause", "detect_anomalies", or "generate_recommendations", the Orchestrator SHALL route the request to the correct corresponding specialized agent

**Validates: Requirements 11.1, 11.2, 11.3, 11.4**

### Property 26: Multi-Agent Execution Sequence

*For any* executive report generation requiring multiple agents, the agents SHALL execute in the sequence: Analysis → Anomaly Detection → Root Cause → Recommendations

**Validates: Requirements 11.5**

### Property 27: Partial Results on Agent Failure

*For any* agent execution failure during multi-agent coordination, the Orchestrator SHALL return partial results from successful agents along with error information

**Validates: Requirements 11.6**

### Property 28: Context Passing Between Agents

*For any* multi-agent workflow, intermediate results from one agent SHALL be passed as context to subsequent agents

**Validates: Requirements 11.7**


### Property 29: Azure OpenAI Retry Logic

*For any* Azure OpenAI request failure, the service SHALL retry up to 3 times with exponential backoff delays of 1s, 2s, and 4s

**Validates: Requirements 12.3**

### Property 30: Service Unavailable After Retries

*For any* Azure OpenAI request where all 3 retry attempts fail, the service SHALL return a service unavailable error

**Validates: Requirements 12.4**

### Property 31: Error Response Structure

*For any* agent processing error, the Backend_API SHALL return a structured error response containing status code, error message, and error type

**Validates: Requirements 9.6**

### Property 32: Request Logging

*For any* API request processed by the Backend_API, a log entry SHALL be created recording the request details and agent interactions

**Validates: Requirements 9.7**

### Property 33: Loading Indicator Display

*For any* API request initiated from the Frontend_Application, a loading indicator SHALL be displayed from request start until response completion

**Validates: Requirements 10.8**

### Property 34: Error Message Display

*For any* API error response received by the Frontend_Application, a user-friendly error message SHALL be displayed to the user

**Validates: Requirements 10.9**

### Property 35: Dataset Restart Clearance

*For any* application restart, all previously stored datasets SHALL be cleared from memory and SHALL NOT be accessible

**Validates: Requirements 14.2**


### Property 36: File Type Validation

*For any* uploaded file with a malicious or non-CSV/Excel extension, the Backend_API SHALL reject the upload

**Validates: Requirements 14.3**

### Property 37: No Disk Persistence

*For any* system operation during MVP execution, no dataset information SHALL be persisted to disk

**Validates: Requirements 14.6**

### Property 38: Sequential Request Processing

*For any* multiple concurrent requests received by the Backend_API, the requests SHALL be processed sequentially (one at a time)

**Validates: Requirements 15.2, 15.3**

### Property 39: Request Queueing Order

*For any* multiple requests received, they SHALL be queued and processed in the order they were received (FIFO)

**Validates: Requirements 15.3**

## Testing Strategy

### Unit Testing

Unit tests verify individual agent methods and utility functions with specific examples and edge cases:

**Understanding Agent Tests:**
- Test column detection with various CSV/Excel formats
- Test data type inference for numeric, categorical, datetime columns
- Test missing value calculation with datasets containing NaN values
- Test edge cases: empty datasets, single-column datasets, all-missing columns

**Analysis Agent Tests:**
- Test KPI calculations with known input/output examples
- Test profit margin formula with sample revenue/profit data
- Test trend calculation with time series data
- Test correlation coefficient calculation
- Test edge cases: zero revenue, negative profit, missing dates


**Anomaly Detection Agent Tests:**
- Test z-score calculation with known outliers
- Test IQR method with sample distributions
- Test rare category detection with categorical data
- Test anomaly score calculation
- Test edge cases: all identical values, single outlier, no outliers

**Recommendation Agent Tests:**
- Test recommendation prioritization logic
- Test minimum recommendation count (at least 3)
- Test recommendation structure validation
- Mock Azure OpenAI responses for recommendation generation

**Orchestrator Tests:**
- Test request routing to correct agents
- Test multi-agent coordination sequence
- Test partial result compilation on agent failure
- Test context passing between agents

### Integration Testing

Integration tests verify end-to-end workflows with mocked Azure OpenAI:

**API Endpoint Tests:**
- Test dataset upload with real CSV/Excel files (1-3 examples)
- Test dataset understanding endpoint response structure
- Test KPI analysis endpoint with demo datasets
- Test anomaly detection endpoint output format
- Test conversational query routing
- Test executive report compilation
- Verify response time constraints with 10,000 row datasets

**Multi-Agent Flow Tests:**
- Test complete executive report generation workflow
- Test agent failure handling and partial results
- Test context propagation through agent chain
- Verify Azure OpenAI retry logic with simulated failures

**Storage Service Tests:**
- Test dataset storage and retrieval
- Test cache expiration behavior
- Test request queue ordering (FIFO)
- Test memory cleanup on restart


### Property-Based Testing

Property tests verify universal properties across randomly generated inputs (minimum 100 iterations per property):

**Property Test 1: File Format Validation**
- Generate random file names with various extensions
- Verify only .csv, .xlsx, .xls pass validation
- **Tag**: Feature: ai-data-analyst-agent, Property 1: File format validation

**Property Test 2: Dataset Round-Trip**
- Generate random DataFrames with varying structures
- Store and retrieve, verify equality
- **Tag**: Feature: ai-data-analyst-agent, Property 3: Dataset storage round-trip

**Property Test 3: Column Detection Completeness**
- Generate DataFrames with random column names
- Verify all columns detected without duplicates
- **Tag**: Feature: ai-data-analyst-agent, Property 4: Column detection completeness

**Property Test 4: Missing Value Percentage**
- Generate DataFrames with random missing values
- Verify percentage = (count / total) * 100
- **Tag**: Feature: ai-data-analyst-agent, Property 7: Missing value percentage relationship

**Property Test 5: Revenue Sum Calculation**
- Generate random revenue data
- Verify total equals sum of all values
- **Tag**: Feature: ai-data-analyst-agent, Property 8: Revenue KPI calculation

**Property Test 6: Profit Margin Formula**
- Generate random profit and revenue values
- Verify margin = (profit / revenue) * 100
- **Tag**: Feature: ai-data-analyst-agent, Property 9: Profit margin relationship

**Property Test 7: Correlation Ranking**
- Generate correlation coefficients
- Verify ranking by descending absolute value
- **Tag**: Feature: ai-data-analyst-agent, Property 11: Correlation coefficient ranking


**Property Test 8: Anomaly Score Assignment**
- Generate random anomaly detections
- Verify all have non-null scores
- **Tag**: Feature: ai-data-analyst-agent, Property 12: Anomaly score assignment

**Property Test 9: Top Anomalies Ranking**
- Generate anomalies with random scores
- Verify top 20 ordered by descending score
- **Tag**: Feature: ai-data-analyst-agent, Property 13: Top anomalies ranking

**Property Test 10: Recommendation Count**
- Generate analysis results
- Verify at least 3 recommendations produced
- **Tag**: Feature: ai-data-analyst-agent, Property 14: Recommendation count minimum

**Property Test 11: Recommendation Prioritization**
- Generate recommendations with impact scores
- Verify ordering by descending impact
- **Tag**: Feature: ai-data-analyst-agent, Property 16: Recommendation prioritization order

**Property Test 12: Agent Routing**
- Generate requests with different types
- Verify each routes to correct agent
- **Tag**: Feature: ai-data-analyst-agent, Property 25: Agent orchestration routing

**Property Test 13: Sequential Processing**
- Generate multiple concurrent requests
- Verify sequential execution order
- **Tag**: Feature: ai-data-analyst-agent, Property 38: Sequential request processing

**Property Test 14: No Disk Writes**
- Monitor file system during operations
- Verify no dataset writes to disk
- **Tag**: Feature: ai-data-analyst-agent, Property 37: No disk persistence

## Deployment Configuration

### Environment Variables

```bash
# Backend (.env)
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_MODEL=gpt-4
BACKEND_PORT=8000
LOG_LEVEL=INFO
MAX_DATASET_ROWS=100000
MAX_DATASET_COLUMNS=50
MAX_FILE_SIZE_MB=50
```


```bash
# Frontend (.env)
REACT_APP_API_BASE_URL=http://localhost:8000/api/v1
REACT_APP_FRONTEND_PORT=3000
```

### Startup Commands

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### Demo Datasets

The system includes three pre-loaded demo datasets in `backend/data/demo_datasets/`:

1. **sales_data.csv**: E-commerce sales data with revenue, profit, product categories, regions
2. **customer_churn.csv**: Customer data with churn indicators, satisfaction scores, tenure
3. **financial_metrics.xlsx**: Monthly financial metrics with KPIs, growth rates, expenses

## Security Considerations

### MVP Security Measures

1. **File Upload Validation**: Extension checking, size limits, content type verification
2. **Input Sanitization**: Pydantic models validate all API inputs
3. **Memory Isolation**: Each dataset stored separately by UUID
4. **No Persistence**: Automatic data cleanup on restart
5. **API Key Security**: Environment variable storage, no hardcoding

### Future Production Considerations

- HTTPS/TLS for API communication
- JWT authentication for multi-user access
- Database encryption at rest
- Rate limiting per user
- Audit logging
- CORS configuration
- Input sanitization against injection attacks


## Performance Considerations

### Optimization Strategies

1. **Caching**: Analysis results cached for 5 minutes to avoid redundant computation
2. **Async Processing**: All Azure OpenAI calls use asyncio for non-blocking execution
3. **Lazy Loading**: Data processed only when requested, not on upload
4. **Batch Processing**: Multiple anomalies explained in single Azure OpenAI call when possible
5. **Memory Management**: Datasets cleared when no longer needed

### Performance Targets

| Operation | Target Time | Dataset Size |
|-----------|-------------|--------------|
| Dataset Understanding | < 5 seconds | 10,000 rows |
| KPI Analysis | < 10 seconds | 10,000 rows |
| Root Cause Analysis | < 15 seconds | 10,000 rows |
| Anomaly Detection | < 15 seconds | 10,000 rows |
| Recommendations | < 10 seconds | Any size |
| Conversational Query | < 8 seconds | Any size |
| Executive Report | < 20 seconds | 10,000 rows |

### Bottleneck Identification

**Potential Bottlenecks:**
1. Azure OpenAI API latency (200-500ms per call)
2. Large dataset parsing (CSV/Excel file I/O)
3. Correlation calculation for many columns (O(n²))
4. Anomaly detection on large datasets

**Mitigation Strategies:**
- Parallel Azure OpenAI calls where possible
- Streaming file parsing for large uploads
- Sample-based correlation for datasets >50 columns
- Incremental anomaly detection with early stopping

## Extensibility and Future Enhancements

### Phase 2 Features (Post-MVP)

1. **Persistent Storage**: PostgreSQL database for multi-user support
2. **Authentication**: User accounts and dataset ownership
3. **Advanced Visualizations**: Interactive charts, drill-down capabilities
4. **Export Functionality**: PDF reports, Excel exports
5. **Scheduled Analysis**: Automatic periodic analysis for uploaded datasets
6. **Custom KPIs**: User-defined KPI formulas and calculations
7. **Advanced Anomaly Detection**: Time series forecasting, clustering-based detection
8. **Multi-Dataset Analysis**: Cross-dataset comparisons and joins
9. **Collaboration**: Shared datasets, comments, annotations
10. **API Webhooks**: Event notifications for completed analyses

### Architecture Extensions

- **Message Queue**: Redis/RabbitMQ for background job processing
- **Distributed Agents**: Microservices architecture with independent agent services
- **Vector Database**: Pinecone/Weaviate for semantic search on analysis history
- **Real-time Streaming**: WebSocket support for live data analysis
- **Multi-Model Support**: Integration with Claude, Gemini alongside GPT-4

---

**Document Version**: 1.0  
**Last Updated**: 2024-01-15  
**Status**: Design Phase Complete
