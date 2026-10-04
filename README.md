# 🚀 Business Orchestration with Autonomous Agentic Workflows & Model Context Protocol (MCP)

> **Real-Time Business Use Case**: Autonomous Credit Card Approval & Underwriting Engine  
> **Tech Stack**: LangChain | LangGraph | FastMCP | Google Gemini | LangSmith Observability | FastAPI | Pydantic

---

## 📌 Executive Summary

Welcome to the **Agentic AI Business Orchestration Workshop**! 

This repository provides a complete, production-grade demonstration of how modern enterprises build autonomous, tool-using, multi-agent AI systems for real-time business operations. Using a **Credit Card Application & Issuance Pipeline** as the business context, this workshop walks you through **3 foundational Agentic Design Patterns**, progressing from single-agent reasoning loops to decoupled Model Context Protocol (MCP) server architectures with autonomous graph-based routing.

---

## 🎯 Workshop Objectives & Core Agentic Patterns

In this workshop, you will explore and execute 3 distinct agentic design patterns:

| Pattern | Module File | Description | Core Technology |
| :--- | :--- | :--- | :--- |
| **1️⃣ ReAct Pattern** | [`src/agentic_workflow/react_agent.py`](src/agentic_workflow/react_agent.py) | **Single Agent with Tool Use**: Reasoning + Action loop where a single LLM agent dynamically selects and executes Python tools based on observations. | LangChain ReAct + Gemini |
| **2️⃣ Supervisor Pattern** | [`src/agentic_workflow/multi_agent.py`](src/agentic_workflow/multi_agent.py) | **Multi-Agent Collaboration**: Hierarchical Leader-Specialist pattern. A Lead Supervisor orchestrates domain-specific sub-agents (Financial Risk, Compliance/KYC) wrapped as tools. | Agent-as-a-Tool Delegation |
| **3️⃣ Agentic Workflow Orchestrator** | [`src/agentic_workflow/agentic_workflow.py`](src/agentic_workflow/agentic_workflow.py)<br>[`src/agentic_workflow/mcp_server.py`](src/agentic_workflow/mcp_server.py)<br>[`src/agentic_workflow/agentic_workflow_mcp.py`](src/agentic_workflow/agentic_workflow_mcp.py) | **Multi-Agent Autonomous Workflow with MCP Tools**: Stateful DAG workflow with **Autonomous Short-Circuit Routing** connected to a decoupled **FastMCP Server** exposing business tools over stdio/HTTP transport. | LangGraph `StateGraph` + FastMCP + `langchain-mcp-adapters` |

---

## 🏗 System Architecture & Workflow Diagram

### Multi-Agent Autonomous Graph Workflow with FastMCP Tool Decoupling

```mermaid
flowchart TD
    subgraph Client ["Client or Business Trigger"]
        A["User or REST API Request"] -->|Application Payload| SG["Shared ApplicationState"]
    end

    subgraph FastMCP_Server ["Model Context Protocol MCP Server"]
        T1["evaluate_financial_risk"]
        T2["verify_kyc_and_fraud"]
        T3["send_customer_notification"]
    end

    subgraph LangGraph_Engine ["LangGraph Autonomous Orchestrator"]
        START([START Node]) --> N1["Node 1: Financial Risk Agent"]
        
        N1 -.- T1

        N1 --> Router{"Autonomous Router"}
        
        Router -->|Financial APPROVED| N2["Node 2: Compliance and KYC Agent"]
        Router -->|Financial REJECTED - Short Circuit| N3["Node 3: Final Underwriter Decision Engine"]
        
        N2 -.- T2
        N2 --> N3
        
        N3 --> N4["Node 4: Customer Notification Engine"]
        N4 -.- T3
        N4 --> END_NODE([END Node])
    end

    SG -.-> LangGraph_Engine
```

---

## 🧩 Deep Dive into the 3 Agentic Patterns

### 1️⃣ Pattern 1: ReAct Pattern (Agent with Tool Use)
- **Concept**: Combines **Reasoning** (chain-of-thought planning) and **Acting** (executing function tools). The agent inspects tool outputs (observations) to decide the next step.
- **Business Demonstration**:
  1. *Inventory & Pricing*: Query stock availability and calculate total order price.
  2. *Credit Card Eligibility*: Check applicant parameters (income, credit score, loan amount, age) and invoke issuance / customer notification tools.
- **Code Reference**: [`src/agentic_workflow/react_agent.py`](src/agentic_workflow/react_agent.py)

### 2️⃣ Pattern 2: Supervisor Pattern (Multi-Agent with Tool Use)
- **Concept**: A primary **Supervisor LLM Agent** manages specialist agents. Each specialist agent (e.g., Financial Risk Specialist, Compliance/KYC Specialist) is encapsulated into an **Agent-as-a-Tool** function wrapper.
- **Business Demonstration**:
  - `Supervisor Agent`: Receives high-level application request -> calls `consult_financial_agent()` tool -> calls `consult_compliance_agent()` tool -> synthesizes findings -> calls `notify_customer()` tool.
- **Code Reference**: [`src/agentic_workflow/multi_agent.py`](src/agentic_workflow/multi_agent.py)

### 3️⃣ Pattern 3: Agentic Workflow Orchestrator Pattern (Autonomous Workflow + MCP)
- **Concept**: Stateful Graph-based DAG orchestration using LangGraph. Decouples business logic tools into a standalone **Model Context Protocol (MCP)** server built with `FastMCP`.
- **Autonomous Conditional Short-Circuiting**:
  - If an applicant fails the Financial Risk assessment (e.g., credit score < 600 or income < $30,000), the **Autonomous Router** (`route_after_financial`) immediately **short-circuits** the workflow to Node 3 (Decision Engine), bypassing Node 2 (Compliance/KYC).
  - *Business Benefit*: Reduces overall pipeline execution latency, cuts LLM token costs, and eliminates unneeded background checks for unqualified leads.
- **MCP Decoupling**:
  - `src/agentic_workflow/mcp_server.py`: Runs a standalone FastMCP server `CreditCardServices`.
  - `src/agentic_workflow/agentic_workflow_mcp.py`: Connects via `stdio_client`, dynamically discovers tools via `load_mcp_tools`, and executes graph nodes asynchronously.
- **Code References**:
  - FastMCP Server: [`src/agentic_workflow/mcp_server.py`](src/agentic_workflow/mcp_server.py)
  - Native LangGraph Workflow: [`src/agentic_workflow/agentic_workflow.py`](src/agentic_workflow/agentic_workflow.py)
  - MCP-Integrated Workflow: [`src/agentic_workflow/agentic_workflow_mcp.py`](src/agentic_workflow/agentic_workflow_mcp.py)

---

## ⚡ Additional Production Modules

### 🌐 1. FastAPI REST API Server
Wraps the LangGraph Credit Card Approval Workflow into an enterprise REST API endpoint with Pydantic validation and health probes.
- **File**: [`src/agentic_workflow/api_server.py`](src/agentic_workflow/api_server.py)
- **Endpoints**:
  - `GET /health`: Liveness & Readiness checks for Kubernetes / AWS ECS.
  - `POST /api/v1/applications/process`: Asynchronous execution of the agentic workflow.

### 📊 2. Workflow Evaluation & Benchmarking Engine
Programmatically benchmarks workflow performance against ground-truth evaluation datasets.
- **File**: [`src/agentic_workflow/workflow_eval.py`](src/agentic_workflow/workflow_eval.py)
- **Key Metrics Evaluated**:
  - **Underwriting Decision Accuracy (%)**
  - **Short-Circuit Router Accuracy (%)**
  - **Average Execution Latency (seconds/run)**

### 🔍 3. Agentic Workflow Observability & LangSmith Tracing Architecture
Provides enterprise-grade trace visibility into DAG graph node execution, tool calls, Gemini LLM prompts/completions, latencies, and dynamic short-circuit router decisions.
- **File**: [`src/agentic_workflow/agentic_workflow.py`](src/agentic_workflow/agentic_workflow.py)

#### 🎯 Key Observability Capabilities
1. **Native LangSmith Tracing**: Automatic trace generation for DAG graph nodes, Gemini LLM prompts/responses, and tool runs enabled via `LANGCHAIN_TRACING_V2=true`.
2. **Span & Node Latency Instrumentation**: High-precision wall-clock latency tracking using `time.perf_counter()` on all DAG agent nodes and short-circuit routers.
3. **Execution Metadata & Dynamic Run Tagging**: Attaches domain attributes (`customer_id`, `income`, `credit_score`, `loan_amount`, `employment_type`) and tags (`credit-score-tier-700`, `agentic-workflow`, LLM model) to every invocation.
4. **Autonomous Conditional Routing Visibility**: Visualizes dynamic graph branching in LangSmith trace trees when a financial rejection short-circuits and skips compliance checks.
5. **Zero-Friction Fallback**: Includes `setup_observability()` which automatically switches to structured local console logging if LangSmith API credentials are not set.

#### ⚙️ Observability Environment Setup (`.env`)
To record workflow execution traces into your LangSmith dashboard, configure the following variables in `.env`:
```env
# LangSmith Telemetry & Tracing Configuration
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_PROJECT=agentic-credit-card-workflow
```

#### 🧩 Code Instrumentation in `agentic_workflow.py`

##### 1. Status Validation & Active Mode Detection (`setup_observability`)
```python
def setup_observability() -> bool:
    """Validates and initializes LangSmith Observability environment settings."""
    tracing_enabled = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    api_key = os.getenv("LANGCHAIN_API_KEY", "")
    project_name = os.getenv("LANGCHAIN_PROJECT", "agentic-credit-card-workflow")
    
    if tracing_enabled and api_key:
        print(f"[OBSERVABILITY]: LangSmith Tracing ACTIVE | Project: '{project_name}'")
        return True
    else:
        print("[OBSERVABILITY]: Local Logging Mode ACTIVE.")
        return False
```

##### 2. RunnableConfig & Metadata Builder (`get_observability_config`)
```python
def get_observability_config(state: ApplicationState, run_name: Optional[str] = None) -> Dict[str, Any]:
    """Generates RunnableConfig containing rich tags and metadata for LangSmith tracing."""
    return {
        "run_name": run_name or f"CreditCardWorkflow-{state.get('applicant_name')}",
        "tags": [
            "agentic-workflow",
            "credit-card-approval",
            f"credit-score-tier-{state.get('credit_score', 0) // 100 * 100}",
            get_valid_gemini_model()
        ],
        "metadata": {
            "applicant_name": state.get("applicant_name"),
            "customer_id": state.get("customer_id"),
            "income": state.get("income", 0.0),
            "credit_score": state.get("credit_score", 0),
            "loan_amount": state.get("loan_amount", 0.0),
            "employment_type": state.get("employment_type", ""),
        }
    }
```

##### 3. Fine-Grained `@traceable` Decorators
- **Tool Spans**: `@traceable(name="evaluate_financial_risk", run_type="tool")` & `@traceable(name="verify_kyc_and_fraud", run_type="tool")`
- **Chain / Node Spans**: `@traceable(name="node_financial_agent", run_type="chain")`, `@traceable(name="node_compliance_agent", run_type="chain")`, `@traceable(name="node_underwriter_decision", run_type="chain")`, `@traceable(name="node_notification_engine", run_type="chain")`
- **Router Edge Spans**: `@traceable(name="route_after_financial", run_type="chain")`

#### 📊 LangSmith Trace Hierarchy Visualizations

##### Path 1: Standard Approval Path (Eligible Applicant - Ayush)
```mermaid
flowchart TD
    Root["Root Run: Run-1-Eligible-Ayush"] --> N1["Span: node_financial_agent"]
    N1 --> T1["Tool Span: evaluate_financial_risk"]
    Root --> R1["Span: route_after_financial (Evaluates True -> compliance_node)"]
    Root --> N2["Span: node_compliance_agent"]
    N2 --> T2["Tool Span: verify_kyc_and_fraud"]
    Root --> N3["Span: node_underwriter_decision"]
    Root --> N4["Span: node_notification_engine"]
```

##### Path 2: Autonomous Short-Circuit Rejection Path (Ineligible Applicant - Rahul)
```mermaid
flowchart TD
    Root["Root Run: Run-2-ShortCircuit-Rahul"] --> N1["Span: node_financial_agent (REJECTED)"]
    N1 --> T1["Tool Span: evaluate_financial_risk"]
    Root --> R1["Span: route_after_financial (Short-Circuit -> decision_node)"]
    Root --> N3["Span: node_underwriter_decision (CARD REJECTED)"]
    Root --> N4["Span: node_notification_engine"]
```

---

## 📁 Repository Directory Structure

```
AGENTIC_WORKFLOW_MCP/
├── .env                       # Environment configuration (git-ignored)
├── .env.example               # Template for environment variables
├── .gitignore                 # Standard Python gitignore rules
├── requirements.txt           # Project dependencies
├── README.md                  # Workshop documentation
└── src/
    ├── __init__.py            # Root package initialization
    └── agentic_workflow/      # Core Agentic AI Business Orchestration Package
        ├── __init__.py        # Package versioning & exports
        ├── react_agent.py     # Pattern 1: ReAct Agent implementation
        ├── multi_agent.py     # Pattern 2: Supervisor Multi-Agent system
        ├── agentic_workflow.py# Pattern 3: LangGraph stateful workflow
        ├── mcp_server.py      # FastMCP standalone tools server
        ├── agentic_workflow_mcp.py # Pattern 3: LangGraph + MCP integration
        ├── api_server.py      # FastAPI REST API wrapper
        └── workflow_eval.py   # Workflow benchmark evaluation engine
```

---

## 🛠 Quickstart & Setup Guide

### Step 1: Prerequisites & Environment Setup
Ensure you have **Python 3.10+** installed. Clone the repository and navigate to the project root.

1. **Create and activate a virtual environment**:
   ```bash
   # Windows (PowerShell)
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install project dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Copy `.env.example` to `.env` (or create `.env`) and set your API keys:
   ```bash
   cp .env.example .env
   ```
   Edit `.env`:
   ```env
   # Gemini API Key
   GOOGLE_API_KEY=your_actual_gemini_api_key_here

   # LangSmith Observability & Tracing Configuration
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
   LANGCHAIN_API_KEY=your_langsmith_api_key_here
   LANGCHAIN_PROJECT=agentic-credit-card-workflow
   ```

---

## 🚀 Workshop Hands-On Execution Guide

Follow these steps sequentially to run every stage of the workshop:

### Step 1️⃣: Run Pattern 1 (ReAct Agent)
Execute the single-agent ReAct reasoning & tool invocation demo:
```bash
python src/agentic_workflow/react_agent.py
# or
python -m src.agentic_workflow.react_agent
```
*Expected Output*: Console trace showing `[USER]`, `[REASONING & ACTION]`, `[OBSERVATION]`, and `[FINAL ANSWER]` steps.

---

### Step 2️⃣: Run Pattern 2 (Supervisor Multi-Agent Pattern)
Execute the multi-agent supervisor collaboration workflow:
```bash
python src/agentic_workflow/multi_agent.py
# or
python -m src.agentic_workflow.multi_agent
```
*Expected Output*: The Lead Supervisor agent invoking `consult_financial_agent`, `consult_compliance_agent`, and `notify_customer` tools to process applicant Ayush.

---

### Step 3️⃣: Run Pattern 3 (Native Stateful LangGraph Workflow with Observability)
Execute the stateful graph orchestrator with autonomous conditional routing and LangSmith telemetry:
```bash
python src/agentic_workflow/agentic_workflow.py
# or
python -m src.agentic_workflow.agentic_workflow
```
*Expected Output*: 
```text
==================================================
--- AUTONOMOUS AGENTIC AI WORKFLOW ORCHESTRATION ---
==================================================
[OBSERVABILITY]: LangSmith Tracing ACTIVE | Project: 'agentic-credit-card-workflow'

>>> RUNNING TEST CASE 1: Eligible Applicant (Ayush)
[WORKFLOW NODE 1]: Financial Risk Agent running...
 -> Financial Risk Agent Result (0.12s): FINANCIAL_STATUS: APPROVED ...
[AUTONOMOUS ROUTER]: Evaluating state after Financial Assessment...
 -> Financial Risk Passed! Routing to Compliance & KYC Agent.
[WORKFLOW NODE 2]: Compliance & KYC Agent running...
 -> Compliance Agent Result (0.08s): COMPLIANCE_STATUS: APPROVED ...
[WORKFLOW NODE 3]: Final Underwriting Decision Node...
 -> Final Decision (0.01s): CARD APPROVED: Credit card issued successfully.
[WORKFLOW NODE 4]: Customer Notification Engine running...
 -> SMS/Email notification delivered to AYUSH: CARD APPROVED ... (0.001s)
[SUMMARY 1]: Final Outcome = CARD APPROVED: Credit card issued successfully. (Total Time: 0.25s)

==================================================
>>> RUNNING TEST CASE 2: Ineligible Applicant (Low Credit Score)
==================================================
[WORKFLOW NODE 1]: Financial Risk Agent running...
 -> Financial Risk Agent Result (0.05s): FINANCIAL_STATUS: REJECTED - Credit score is below 600.
[AUTONOMOUS ROUTER]: Evaluating state after Financial Assessment...
 -> Financial Risk Failed! Short-circuiting workflow directly to Final Decision.
[WORKFLOW NODE 3]: Final Underwriting Decision Node...
 -> Final Decision (0.001s): CARD REJECTED: Financial Risk Check Failed ...
[WORKFLOW NODE 4]: Customer Notification Engine running...
 -> SMS/Email notification delivered to RAHUL: CARD REJECTED ... (0.001s)
[SUMMARY 2]: Final Outcome = CARD REJECTED: Financial Risk Check Failed ... (Total Time: 0.06s)
```

---

### Step 4️⃣: Run Pattern 3 with Model Context Protocol (FastMCP)
Execute the complete decoupling pattern where LangGraph dynamically connects to FastMCP via stdio transport:
```bash
python src/agentic_workflow/agentic_workflow_mcp.py
# or
python -m src.agentic_workflow.agentic_workflow_mcp
```
*Expected Output*:
```text
Connecting to MCP Server ...
MCP Session Initialized!
Discovered MCP Tools: ['evaluate_financial_risk', 'verify_kyc_and_fraud', 'send_customer_notification']
...
[WORKFLOW NODE 1 - MCP]: Financial Risk Agent running...
 -> MCP Financial Tool Output: FINANCIAL_STATUS: APPROVED ...
```

---

### Step 5️⃣: Launch Production FastAPI REST Server
Start the production Uvicorn server:
```bash
python src/agentic_workflow/api_server.py
# or
python -m src.agentic_workflow.api_server
```
The API server will launch at `http://localhost:8000`.

- **Swagger Documentation**: Open [http://localhost:8000/docs](http://localhost:8000/docs) in your browser.
- **Test Application via curl**:
  ```bash
  curl -X POST "http://localhost:8000/api/v1/applications/process" \
       -H "Content-Type: application/json" \
       -d '{
             "applicant_name": "Ayush Kumar",
             "customer_id": "ID-998811",
             "income": 65000.0,
             "credit_score": 720,
             "loan_amount": 4000.0,
             "employment_type": "Salaried"
           }'
  ```

---

### Step 6️⃣: Run Automated Workflow Benchmark Evaluation
Run the evaluation suite against ground-truth datasets:
```bash
python src/agentic_workflow/workflow_eval.py
# or
python -m src.agentic_workflow.workflow_eval
```
*Expected Output*:
```text
==================================================
--- EVALUATION BENCHMARK SUMMARY REPORT ---
==================================================
Total Test Cases Evaluated   : 4
Underwriting Decision Accuracy: 100.0%
Short-Circuit Router Accuracy : 100.0%
Average Execution Latency    : 2.15 seconds/run
==================================================
```

---

## 💡 Key Architecture Takeaways for Enterprise Engineers

1. **Why Model Context Protocol (MCP)?**
   - **Decoupling**: Business tools live in isolated services (`FastMCP`) independent of the agent framework or LLM provider.
   - **Reusability**: The same FastMCP tools can be reused by Claude, Gemini, ChatGPT, or custom LangGraph clients without code duplication.

2. **Why LangGraph for Business Orchestration?**
   - Standard LLM chains are static. LangGraph provides **durable state persistence**, **dynamic graph routing**, and **deterministic short-circuiting** essential for complex financial workflows.

3. **Why Continuous Evaluation Benchmarks?**
   - Non-deterministic LLMs require rigorous testing. Automated evaluation ensures that routing logic, decision accuracy, and SLA latency targets are consistently met before deploying to production.

---

## 📄 License & Attribution

Created for the **Autonomous Agentic AI & MCP Business Orchestration Workshop**. Built with [LangChain](https://www.langchain.com/), [LangGraph](https://www.langchain.com/langgraph), [FastMCP](https://github.com/jlowin/fastmcp), and Google Gemini.
