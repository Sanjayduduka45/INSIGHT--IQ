# Implementation Plan: AI Data Analyst Agent

## Overview

This implementation plan details the step-by-step development of a multi-agent AI system for automated data analysis. The system consists of a Python FastAPI backend with four specialized agents (Understanding, Analysis, Anomaly Detection, Recommendation) orchestrated by a central agent, and a React frontend providing interactive dashboards and chat interface. Implementation follows an incremental approach: project setup → backend core → agents → API layer → frontend → integration → testing.

## Tasks

- [ ] 1. Project setup and configuration
  - Create root project directory structure
  - Set up backend Python project with virtual environment
  - Set up frontend React project with Vite
  - Create environment configuration files (.env.example for both backend and frontend)
  - Initialize Git repository with appropriate .gitignore files
  - Create README.md with setup instructions
  - _Requirements: 13.1, 13.2, 13.3, 13.5, 13.6_

- [ ] 2. Backend core infrastructure
  - [ ] 2.1 Implement configuration and utilities
    - Create `backend/app/config.py` for environment variable management
    - Implement `backend/app/utils/logger.py` for structured logging
    - Implement `backend/app/utils/validators.py` for input validation helpers
    - _Requirements: 9.7, 9.8, 14.3, 14.4_

  - [ ] 2.2 Implement in-memory storage service
    - Create `backend/app/services/storage_service.py` with InMemoryStorageService class
    - Implement dataset storage with UUID generation
    - Implement dataset retrieval and deletion methods
    - Implement analysis results caching with key-based access
    - Implement request queue for sequential processing
    - _Requirements: 9.3, 15.1, 15.2, 15.3, 14.1, 14.2_

  - [ ]* 2.3 Write property tests for storage service
    - **Property 3: Dataset Storage Round-Trip**
    - **Validates: Requirements 1.5**
    - Test that storing and retrieving a dataset returns identical content and structure
    - Generate random DataFrames and verify round-trip equality (100+ iterations)

  - [ ] 2.4 Implement Azure OpenAI service
    - Create `backend/app/services/azure_openai_service.py` with AzureOpenAIService class
    - Implement completion method with retry logic and exponential backoff (1s, 2s, 4s delays)
    - Implement rate limiting with semaphore (max 5 concurrent requests)
    - Implement JSON response parsing for structured outputs
    - Add error handling for service unavailability after 3 retries
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6_

  - [ ]* 2.5 Write property tests for Azure OpenAI retry logic
    - **Property 29: Azure OpenAI Retry Logic**
    - **Validates: Requirements 12.3**
    - Test that failed requests retry up to 3 times with exponential backoff
    - **Property 30: Service Unavailable After Retries**
    - **Validates: Requirements 12.4**
    - Test that after 3 failed retries, service unavailable error is returned

  - [ ] 2.6 Implement dataset service
    - Create `backend/app/services/dataset_service.py` with DatasetService class
    - Implement CSV file parsing using pandas
    - Implement Excel file parsing (.xlsx, .xls) using pandas with openpyxl
    - Implement file format validation (extension checking)
    - Implement file size validation (50MB limit)
    - Implement dataset size validation (100k rows, 50 columns limits)
    - _Requirements: 1.1, 1.2, 1.3, 1.6, 1.7, 14.3, 14.4_

  - [ ]* 2.7 Write property tests for file validation
    - **Property 1: File Format Validation**
    - **Validates: Requirements 1.1, 1.2, 1.3**
    - Generate random file names with various extensions, verify only .csv, .xlsx, .xls pass
    - **Property 36: File Type Validation**
    - **Validates: Requirements 14.3**
    - Test that malicious or non-CSV/Excel extensions are rejected

- [ ] 3. Implement base agent infrastructure
  - [ ] 3.1 Create base agent abstract class
    - Create `backend/app/agents/base_agent.py` with BaseAgent ABC
    - Define abstract `analyze()` method signature
    - Define abstract `validate_input()` method signature
    - Implement standardized `handle_error()` method for error responses
    - Initialize Azure OpenAI service dependency injection
    - _Requirements: 9.4, 9.6, 11.7_

  - [ ] 3.2 Define Pydantic models for data structures
    - Create `backend/app/models/dataset.py` with dataset metadata models
    - Create `backend/app/models/analysis.py` with KPI, correlation, anomaly models
    - Create `backend/app/models/response.py` with standardized API response models
    - _Requirements: 9.2_

- [ ] 4. Implement specialized agents
  - [ ] 4.1 Implement Understanding Agent
    - Create `backend/app/agents/understanding_agent.py` extending BaseAgent
    - Implement `analyze()` method for dataset schema detection
    - Implement `_infer_type()` helper for data type inference (numeric, categorical, datetime)
    - Implement `_categorize_column()` helper for column categorization
    - Implement missing value count and percentage calculation
    - Implement `validate_input()` to check dataset is not empty
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8_

  - [ ]* 4.2 Write property tests for Understanding Agent
    - **Property 4: Column Detection Completeness**
    - **Validates: Requirements 2.1**
    - Generate DataFrames with random column names, verify all detected without duplicates
    - **Property 5: Data Type Inference Consistency**
    - **Validates: Requirements 2.2, 2.5, 2.6, 2.7**
    - Test correct identification of numeric, categorical, datetime columns
    - **Property 6: Missing Value Count Accuracy**
    - **Validates: Requirements 2.3**
    - Verify count equals actual number of NaN values
    - **Property 7: Missing Value Percentage Relationship**
    - **Validates: Requirements 2.4**
    - Verify percentage = (missing_count / total_rows) * 100

  - [ ] 4.3 Implement Analysis Agent
    - Create `backend/app/agents/analysis_agent.py` extending BaseAgent
    - Implement `analyze()` method routing to KPI or root cause analysis
    - Implement `_calculate_kpis()` for KPI computation (revenue, profit, churn, growth, retention)
    - Implement `_identify_kpi_columns()` using Azure OpenAI for column mapping
    - Implement `_calculate_trend()` helper for time series trends
    - Implement `_calculate_growth_rate()` helper for customer growth metrics
    - Implement `_analyze_root_cause()` for correlation and categorical analysis
    - Implement `_generate_root_cause_explanation()` using Azure OpenAI
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_

  - [ ]* 4.4 Write property tests for Analysis Agent
    - **Property 8: Revenue KPI Calculation**
    - **Validates: Requirements 3.1**
    - Generate random revenue data, verify total equals sum of all values
    - **Property 9: Profit Margin Relationship**
    - **Validates: Requirements 3.4**
    - Generate random profit/revenue values, verify margin = (profit / revenue) * 100
    - **Property 10: Churn Rate Calculation**
    - **Validates: Requirements 3.5**
    - Verify churn rate = (sum_of_churn_indicators / total_rows) * 100
    - **Property 11: Correlation Coefficient Ranking**
    - **Validates: Requirements 4.5**
    - Verify ranking ordered by descending absolute correlation value

  - [ ] 4.5 Implement Anomaly Detection Agent
    - Create `backend/app/agents/anomaly_detection_agent.py` extending BaseAgent
    - Implement `analyze()` method for multi-method anomaly detection
    - Implement `_detect_numeric_anomalies()` using z-score and IQR methods
    - Implement `_detect_categorical_anomalies()` using frequency analysis (< 1% threshold)
    - Implement `_calculate_anomaly_score()` for ranking anomalies
    - Implement `_generate_anomaly_explanation()` using Azure OpenAI
    - Return top 20 anomalies ranked by score
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8_

  - [ ]* 4.6 Write property tests for Anomaly Detection Agent
    - **Property 12: Anomaly Score Assignment**
    - **Validates: Requirements 5.2**
    - Generate random anomalies, verify all have non-null scores
    - **Property 13: Top Anomalies Ranking**
    - **Validates: Requirements 5.7**
    - Generate anomalies with random scores, verify top 20 ordered by descending score

  - [ ] 4.7 Implement Recommendation Agent
    - Create `backend/app/agents/recommendation_agent.py` extending BaseAgent
    - Implement `analyze()` method for recommendation generation
    - Implement `_generate_recommendations()` using Azure OpenAI with KPI/root cause/anomaly context
    - Implement `_prioritize_recommendations()` to sort by impact score (high=3, medium=2, low=1)
    - Ensure at least 3 recommendations are generated
    - Include reasoning text for each recommendation
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8_

  - [ ]* 4.8 Write property tests for Recommendation Agent
    - **Property 14: Recommendation Count Minimum**
    - **Validates: Requirements 6.6**
    - Generate analysis results, verify at least 3 recommendations produced
    - **Property 15: Recommendation Reasoning Presence**
    - **Validates: Requirements 6.7**
    - Verify each recommendation includes non-empty reasoning text
    - **Property 16: Recommendation Prioritization Order**
    - **Validates: Requirements 6.5**
    - Generate recommendations with impact scores, verify ordering by descending impact

- [ ] 5. Checkpoint - Verify agent implementations
  - Ensure all agents extend BaseAgent correctly
  - Run property tests for all agents and verify they pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Implement orchestrator agent
  - [ ] 6.1 Create orchestrator agent
    - Create `backend/app/agents/orchestrator.py` with OrchestratorAgent class
    - Initialize with all four specialized agents via dependency injection
    - Implement `process_request()` method for request routing
    - Implement routing logic for: understand, analyze_kpi, root_cause, detect_anomalies, generate_recommendations
    - Implement `_generate_executive_report()` for multi-agent coordination
    - Implement `_handle_conversational_query()` for natural language routing
    - Implement `_classify_query_intent()` using Azure OpenAI
    - Implement partial results handling when agents fail
    - Implement context passing between agents in multi-step workflows
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 7.1, 7.2, 7.3, 8.1, 8.2_

  - [ ]* 6.2 Write property tests for orchestrator
    - **Property 25: Agent Orchestration Routing**
    - **Validates: Requirements 11.1, 11.2, 11.3, 11.4**
    - Generate requests with different types, verify each routes to correct agent
    - **Property 26: Multi-Agent Execution Sequence**
    - **Validates: Requirements 11.5**
    - Verify executive report generation executes agents in correct sequence
    - **Property 27: Partial Results on Agent Failure**
    - **Validates: Requirements 11.6**
    - Simulate agent failures, verify partial results returned with error information
    - **Property 28: Context Passing Between Agents**
    - **Validates: Requirements 11.7**
    - Verify intermediate results passed as context to subsequent agents

- [ ] 7. Implement FastAPI backend server
  - [ ] 7.1 Create FastAPI application entry point
    - Create `backend/app/main.py` with FastAPI application instance
    - Configure CORS middleware for frontend communication
    - Initialize all services (storage, Azure OpenAI, dataset)
    - Initialize all agents and orchestrator with dependency injection
    - Add exception handlers for standardized error responses
    - Add startup event to log application initialization
    - Add shutdown event to clear in-memory storage
    - _Requirements: 9.1, 9.2, 9.6, 13.1, 14.2, 14.5_

  - [ ] 7.2 Implement dataset management endpoints
    - Create `backend/app/api/routes/dataset.py`
    - Implement POST `/api/v1/datasets/upload` for file upload
    - Implement GET `/api/v1/datasets/{datasetId}` for metadata retrieval
    - Implement DELETE `/api/v1/datasets/{datasetId}` for dataset deletion
    - Add file validation, size checks, and error responses
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 9.2_

  - [ ]* 7.3 Write property tests for dataset endpoints
    - **Property 2: File Upload Error Messaging**
    - **Validates: Requirements 1.4**
    - Test invalid uploads return non-empty error messages describing validation failures

  - [ ] 7.4 Implement analysis endpoints
    - Create `backend/app/api/routes/analysis.py`
    - Implement GET `/api/v1/analysis/{datasetId}/understand` for dataset understanding
    - Implement GET `/api/v1/analysis/{datasetId}/kpi` for KPI calculation
    - Implement POST `/api/v1/analysis/{datasetId}/root-cause` for root cause analysis
    - Implement GET `/api/v1/analysis/{datasetId}/anomalies` for anomaly detection
    - Implement GET `/api/v1/analysis/{datasetId}/recommendations` for recommendations
    - Route all requests through orchestrator agent
    - Add response time logging and performance tracking
    - _Requirements: 2.8, 3.9, 4.7, 5.8, 6.8_

  - [ ] 7.5 Implement chat and report endpoints
    - Create `backend/app/api/routes/chat.py` with POST `/api/v1/chat/{datasetId}/ask`
    - Create `backend/app/api/routes/report.py` with GET `/api/v1/analysis/{datasetId}/report`
    - Implement conversational query handling with intent classification
    - Implement executive report compilation with all agent results
    - Add visualization configuration generation for chart responses
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9_

  - [ ]* 7.6 Write property tests for API endpoints
    - **Property 17: Query Routing Correctness**
    - **Validates: Requirements 7.3**
    - Generate queries with KPI keywords, verify routing to Analysis Agent
    - **Property 19: Chart Configuration Validity**
    - **Validates: Requirements 7.6**
    - Verify visualization responses contain valid chart type and data structure
    - **Property 20-23: Executive Report Completeness**
    - **Validates: Requirements 8.1, 8.4, 8.5, 8.6**
    - Verify report includes all required components from agents
    - **Property 31: Error Response Structure**
    - **Validates: Requirements 9.6**
    - Verify error responses contain status code, message, and error type

  - [ ] 7.7 Implement API dependencies and middleware
    - Create `backend/app/api/dependencies.py` with dependency injection functions
    - Implement dataset retrieval dependency with validation
    - Implement request queue middleware for sequential processing
    - Add logging middleware for request/response tracking
    - _Requirements: 9.7, 15.2, 15.3_

  - [ ]* 7.8 Write property tests for request processing
    - **Property 38: Sequential Request Processing**
    - **Validates: Requirements 15.2, 15.3**
    - Generate multiple concurrent requests, verify sequential execution
    - **Property 39: Request Queueing Order**
    - **Validates: Requirements 15.3**
    - Verify requests processed in FIFO order

  - [ ] 7.9 Create backend startup script
    - Create `backend/run.py` for application startup
    - Configure uvicorn server with configurable port (default 8000)
    - Add environment variable loading
    - Add graceful shutdown handling
    - _Requirements: 13.1, 13.6_

- [ ] 8. Checkpoint - Backend integration testing
  - Test all API endpoints with demo datasets
  - Verify multi-agent workflows execute correctly
  - Verify error handling and partial results
  - Ensure performance targets met for 10k row datasets
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. Implement React frontend application
  - [ ] 9.1 Create frontend project structure
    - Initialize React project with Vite
    - Install dependencies: Material-UI, Axios, Recharts, React Router
    - Create folder structure for components, services, context
    - Create `frontend/src/index.js` entry point
    - Create `frontend/src/App.jsx` main component with routing
    - _Requirements: 10.1, 13.2_

  - [ ] 9.2 Implement API service layer
    - Create `frontend/src/services/api.js` with Axios client
    - Configure base URL from environment variables
    - Implement dataset upload API call with FormData
    - Implement all analysis API calls (understand, KPI, anomalies, recommendations, report)
    - Implement chat API call
    - Implement error handling and response parsing
    - _Requirements: 10.9, 13.3, 14.5_

  - [ ] 9.3 Implement context for state management
    - Create `frontend/src/context/DataContext.jsx` with React Context
    - Implement state for current dataset ID, analysis results, loading states, errors
    - Implement context provider component wrapping application
    - _Requirements: 10.1_

  - [ ] 9.4 Implement common components
    - Create `frontend/src/components/Common/LoadingIndicator.jsx` with MUI CircularProgress
    - Create `frontend/src/components/Common/ErrorMessage.jsx` with MUI Alert
    - Create `frontend/src/components/Common/Header.jsx` with navigation
    - _Requirements: 10.8, 10.9_

- [ ] 10. Implement frontend feature components
  - [ ] 10.1 Implement file upload component
    - Create `frontend/src/components/FileUpload/FileUpload.jsx`
    - Implement file input with CSV/Excel validation
    - Implement file size validation (50MB limit)
    - Implement upload progress indicator
    - Implement error display for invalid uploads
    - Call dataset upload API on file selection
    - Update context with dataset ID on successful upload
    - _Requirements: 10.2, 10.8, 10.9_

  - [ ] 10.2 Implement dataset overview dashboard
    - Create `frontend/src/components/Dashboard/DatasetOverview.jsx`
    - Fetch dataset understanding from API
    - Display column information table (name, type, missing %)
    - Display row and column counts
    - Show loading indicator during fetch
    - _Requirements: 10.3, 10.8_

  - [ ] 10.3 Implement KPI analysis dashboard
    - Create `frontend/src/components/Dashboard/KPIAnalysisDashboard.jsx`
    - Fetch KPI analysis from API
    - Display KPI metrics in card layout using MUI Grid
    - Display revenue trend chart using Recharts
    - Show loading indicator during analysis
    - _Requirements: 10.4, 10.8_

  - [ ] 10.4 Implement anomaly detection view
    - Create `frontend/src/components/Dashboard/AnomalyDetectionView.jsx`
    - Fetch anomaly detection results from API
    - Display top anomalies table with row index, column, value, score, explanation
    - Sort by anomaly score (highest first)
    - Show loading indicator during detection
    - _Requirements: 10.5, 10.8_

  - [ ] 10.5 Implement chat interface
    - Create `frontend/src/components/Chat/ChatInterface.jsx`
    - Create `frontend/src/components/Chat/ChatMessage.jsx` for message display
    - Implement message list with user/assistant role styling
    - Implement input field and send button
    - Call chat API on message send
    - Display loading indicator while waiting for response
    - Handle visualization data in responses
    - _Requirements: 10.6, 7.8, 10.8_

  - [ ] 10.6 Implement executive report view
    - Create `frontend/src/components/Report/ExecutiveReport.jsx`
    - Fetch executive report from API
    - Display KPIs summary section
    - Display top 3 root causes section
    - Display top 5 anomalies section
    - Display top 5 recommendations section
    - Format in business-appropriate layout using MUI components
    - _Requirements: 10.7, 10.8_

  - [ ] 10.7 Wire components in main application
    - Update `frontend/src/App.jsx` with routing
    - Add routes for upload, dashboard, chat, report views
    - Integrate DataContext provider
    - Add navigation in Header component
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7_

- [ ] 11. Checkpoint - Frontend integration
  - Test all frontend components with backend API
  - Verify loading indicators display correctly
  - Verify error messages display correctly
  - Test end-to-end user workflows
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 12. Create demo datasets and documentation
  - [ ] 12.1 Create demo datasets
    - Create `backend/data/demo_datasets/sales_data.csv` with e-commerce sales data
    - Create `backend/data/demo_datasets/customer_churn.csv` with customer churn data
    - Create `backend/data/demo_datasets/financial_metrics.xlsx` with financial KPIs
    - Ensure datasets have appropriate columns for testing all features
    - _Requirements: 13.4, 13.7_

  - [ ] 12.2 Create setup and usage documentation
    - Create `docs/setup.md` with local deployment instructions
    - Create `docs/api_documentation.md` with API endpoint reference
    - Create `docs/architecture.md` with system architecture details
    - Update root `README.md` with project overview and quick start
    - Document environment variables in `.env.example` files
    - Document performance benchmarks
    - _Requirements: 13.5, 13.6, 15.7_

- [ ] 13. Integration testing and validation
  - [ ]* 13.1 Write integration tests for multi-agent workflows
    - Test complete executive report generation workflow
    - Test context propagation through agent chain
    - Verify Azure OpenAI retry logic with simulated failures
    - Test storage service integration with agents

  - [ ]* 13.2 Write integration tests for API endpoints
    - Test dataset upload with real CSV/Excel files
    - Test dataset understanding endpoint response structure
    - Test KPI analysis endpoint with demo datasets
    - Test anomaly detection endpoint output format
    - Test conversational query routing
    - Test executive report compilation
    - Verify response time constraints with 10,000 row datasets

  - [ ] 13.3 Perform end-to-end testing
    - Test complete user workflow: upload → understand → analyze → report
    - Test conversational analytics with various question types
    - Test error handling scenarios (invalid files, missing datasets, API failures)
    - Test with all three demo datasets
    - Verify performance targets are met

  - [ ]* 13.4 Write property tests for data persistence
    - **Property 24: In-Memory Storage Verification**
    - **Validates: Requirements 9.3**
    - Verify dataset retrievable from memory with no disk writes
    - **Property 35: Dataset Restart Clearance**
    - **Validates: Requirements 14.2**
    - Test that application restart clears all stored datasets
    - **Property 37: No Disk Persistence**
    - **Validates: Requirements 14.6**
    - Monitor file system during operations, verify no dataset writes to disk

  - [ ] 13.5 Verify security and validation
    - Test file upload validation rejects malicious file types
    - Test file size limits enforced (50MB)
    - Test dataset size limits enforced (100k rows, 50 columns)
    - Verify environment variables loaded correctly
    - Test CORS configuration allows frontend requests
    - _Requirements: 14.3, 14.4, 14.5_

- [ ] 14. Final checkpoint - System validation
  - Start both backend and frontend servers
  - Perform complete demonstration workflow with all three demo datasets
  - Verify all features work as expected
  - Verify error handling and edge cases
  - Verify performance meets targets
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional testing sub-tasks that can be skipped for faster MVP
- Each task references specific requirements from the requirements document for traceability
- Property-based tests validate universal correctness properties across all inputs
- Checkpoints ensure incremental validation and provide opportunities for user feedback
- Backend implemented in **Python** with FastAPI, Pandas, NumPy, SciPy, scikit-learn, Azure OpenAI SDK
- Frontend implemented in **JavaScript/React** with Material-UI, Axios, Recharts
- System uses in-memory storage for MVP (no database required)
- All Azure OpenAI calls include retry logic with exponential backoff
- Multi-agent architecture follows orchestrator pattern with four specialized agents
- Sequential task processing ensures single-user MVP demonstration requirements


## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1"] },
    { "id": 1, "tasks": ["2.1", "2.2"] },
    { "id": 2, "tasks": ["2.3", "2.4", "2.6"] },
    { "id": 3, "tasks": ["2.5", "2.7", "3.1", "3.2"] },
    { "id": 4, "tasks": ["4.1"] },
    { "id": 5, "tasks": ["4.2", "4.3"] },
    { "id": 6, "tasks": ["4.4", "4.5"] },
    { "id": 7, "tasks": ["4.6", "4.7"] },
    { "id": 8, "tasks": ["4.8", "6.1"] },
    { "id": 9, "tasks": ["6.2", "7.1"] },
    { "id": 10, "tasks": ["7.2", "7.4", "7.5", "7.7"] },
    { "id": 11, "tasks": ["7.3", "7.6", "7.8", "7.9"] },
    { "id": 12, "tasks": ["9.1"] },
    { "id": 13, "tasks": ["9.2", "9.3", "9.4"] },
    { "id": 14, "tasks": ["10.1"] },
    { "id": 15, "tasks": ["10.2", "10.3", "10.4"] },
    { "id": 16, "tasks": ["10.5", "10.6"] },
    { "id": 17, "tasks": ["10.7"] },
    { "id": 18, "tasks": ["12.1", "12.2"] },
    { "id": 19, "tasks": ["13.1", "13.2"] },
    { "id": 20, "tasks": ["13.3", "13.4", "13.5"] }
  ]
}
```
