"""
Autonomous Agentic AI Workflow Orchestration System with Observability
---------------------------------------------------------------------
This file demonstrates Graph-Based Workflow Orchestration for an Autonomous Credit Card Approval System 
using LangGraph, LangChain, and LangSmith Observability.

Key Observability Capabilities Demonstrated:
1. Native LangSmith Tracing: Automatic execution trace emission for DAG graph steps, LLM calls, and tool runs.
2. Span & Node Latency Instrumentation: Tracking execution time across nodes and short-circuit routers.
3. Execution Metadata & Tags: Attaching customer ID, applicant name, credit score, and status tags to runs.
4. Autonomous Conditional Routing Visibility: Full tracing of short-circuit decisions.
"""

import os
import sys
import time
from pathlib import Path
from typing import TypedDict, Literal, Optional, Dict, Any

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, START, END

# Import LangSmith traceable decorator with fallback if langsmith is not installed
try:
    from langsmith import traceable
except ImportError:
    def traceable(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

# 1. Load environment variables
load_dotenv()

# ==========================================
# 1. SHARED GRAPH STATE DEFINITION
# ==========================================
class ApplicationState(TypedDict):
    applicant_name: str
    income: float
    credit_score: int
    loan_amount: float
    employment_type: str
    customer_id: str
    
    # Workflow intermediate state populated by Agent Nodes
    financial_assessment: str
    is_financial_approved: bool
    
    compliance_assessment: str
    is_compliance_approved: bool
    
    final_decision: str
    notification_log: str


# ==========================================
# 0. OBSERVABILITY SETUP & CONFIGURATION
# ==========================================
def setup_observability() -> bool:
    """
    Validates and initializes LangSmith Observability environment settings.
    Returns True if tracing is active, False otherwise.
    """
    tracing_enabled = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    api_key = os.getenv("LANGCHAIN_API_KEY", "")
    project_name = os.getenv("LANGCHAIN_PROJECT", "agentic-credit-card-workflow")
    
    if tracing_enabled and api_key:
        print(f"[OBSERVABILITY]: LangSmith Tracing ACTIVE | Project: '{project_name}'")
        return True
    else:
        print("[OBSERVABILITY]: Local Logging Mode ACTIVE. (Set LANGCHAIN_TRACING_V2=true and LANGCHAIN_API_KEY for LangSmith UI Tracing)")
        return False


def get_observability_config(state: ApplicationState, run_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Generates a LangChain RunnableConfig dict containing rich tags and metadata
    for end-to-end execution tracing in LangSmith.
    """
    applicant = state.get("applicant_name", "Unknown")
    customer_id = state.get("customer_id", "N/A")
    credit_score = state.get("credit_score", 0)
    
    return {
        "run_name": run_name or f"CreditCardWorkflow-{applicant}",
        "tags": [
            "agentic-workflow",
            "credit-card-approval",
            f"credit-score-tier-{credit_score // 100 * 100}",
            get_valid_gemini_model()
        ],
        "metadata": {
            "applicant_name": applicant,
            "customer_id": customer_id,
            "income": state.get("income", 0.0),
            "credit_score": credit_score,
            "loan_amount": state.get("loan_amount", 0.0),
            "employment_type": state.get("employment_type", ""),
        }
    }


# ==========================================
# 2. TOOLS FOR SPECIALIZED AGENT NODES (INSTRUMENTED)
# ==========================================
@tool
@traceable(name="evaluate_financial_risk", run_type="tool")
def evaluate_financial_risk(income: float, credit_score: int, loan_amount: float) -> str:
    """Evaluates credit score, income, and debt ratio."""
    if credit_score < 600:
        return "FINANCIAL_STATUS: REJECTED - Credit score is below 600."
    if income < 30000:
        return "FINANCIAL_STATUS: REJECTED - Annual income is below $30,000 threshold."
    if loan_amount > (income * 0.5):
        return "FINANCIAL_STATUS: REJECTED - Existing loan exceeds 50% of annual income."
    return "FINANCIAL_STATUS: APPROVED - Financial parameters meet risk criteria."

@tool
@traceable(name="verify_kyc_and_fraud", run_type="tool")
def verify_kyc_and_fraud(customer_id: str, employment_type: str) -> str:
    """Verifies customer ID validity and employment classification."""
    if not customer_id or len(customer_id) < 5:
        return "COMPLIANCE_STATUS: REJECTED - Customer ID validation failed."
    if employment_type.lower() not in ["salaried", "self-employed"]:
        return "COMPLIANCE_STATUS: REJECTED - Employment type not supported."
    return "COMPLIANCE_STATUS: APPROVED - Background check and KYC passed."


def get_valid_google_api_key() -> str:
    """Safely retrieves the Gemini API key, filtering out invalid dummy placeholders."""
    for env_var in ["GEMINI_API_KEY", "GOOGLE_API_KEY"]:
        val = os.getenv(env_var, "").strip()
        if val and not val.startswith("AQ.Ab") and "your_" not in val.lower() and val != "placeholder_key":
            return val
    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "placeholder_key"


def get_valid_gemini_model() -> str:
    """Returns a valid Gemini generation model name."""
    model = os.getenv("GEMINI_GENERATION_MODEL") or os.getenv("GEMINI_MODEL") or "gemini-1.5-flash"
    if model in ["gemini-3.5-flash-lite", "gemini-2.5-flash"]:
        return "gemini-1.5-flash"
    return model


# Initialize Gemini LLM (Uses valid API key & model)
google_api_key = get_valid_google_api_key()
model_name = get_valid_gemini_model()
#llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")
llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=google_api_key)

# Create specialized agents
financial_agent = create_react_agent(llm, [evaluate_financial_risk])
compliance_agent = create_react_agent(llm, [verify_kyc_and_fraud])


def extract_text_content(content) -> str:
    """Helper to safely extract string text from LLM response content (handles lists and dicts)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list) and len(content) > 0:
        if isinstance(content[0], dict) and "text" in content[0]:
            return content[0]["text"]
        return str(content[0])
    return str(content)


# ==========================================
# 3. WORKFLOW AGENT NODES (INSTRUMENTED WITH SPANS & LATENCY)
# ==========================================
@traceable(name="node_financial_agent", run_type="chain")
def node_financial_agent(state: ApplicationState) -> ApplicationState:
    """Node 1: Financial Risk Assessment Agent Node"""
    start_time = time.perf_counter()
    print("\n[WORKFLOW NODE 1]: Financial Risk Agent running...")
    prompt = (
        f"Evaluate financial risk for customer {state['applicant_name']} "
        f"with Income: ${state['income']}, Credit Score: {state['credit_score']}, "
        f"Loan Amount: ${state['loan_amount']}."
    )
    try:
        res = financial_agent.invoke({"messages": [("user", prompt)]})
        output_text = extract_text_content(res["messages"][-1].content)
    except Exception as e:
        print(f" -> [Agent Warning]: Agent LLM loop issue ({e}), executing tool directly...")
        output_text = evaluate_financial_risk.invoke({
            "income": state["income"],
            "credit_score": state["credit_score"],
            "loan_amount": state["loan_amount"]
        })
        output_text = extract_text_content(output_text)

    is_approved = "REJECTED" not in output_text.upper()
    duration = round(time.perf_counter() - start_time, 3)
    print(f" -> Financial Risk Agent Result ({duration}s): {output_text.strip()}")
    
    return {
        "financial_assessment": output_text,
        "is_financial_approved": is_approved
    }


@traceable(name="node_compliance_agent", run_type="chain")
def node_compliance_agent(state: ApplicationState) -> ApplicationState:
    """Node 2: Compliance & KYC Agent Node"""
    start_time = time.perf_counter()
    print("\n[WORKFLOW NODE 2]: Compliance & KYC Agent running...")
    prompt = (
        f"Perform KYC and background check for Customer ID: {state['customer_id']}, "
        f"Employment Type: {state['employment_type']}."
    )
    try:
        res = compliance_agent.invoke({"messages": [("user", prompt)]})
        output_text = extract_text_content(res["messages"][-1].content)
    except Exception as e:
        print(f" -> [Agent Warning]: Agent LLM loop issue ({e}), executing tool directly...")
        output_text = verify_kyc_and_fraud.invoke({
            "customer_id": state["customer_id"],
            "employment_type": state["employment_type"]
        })
        output_text = extract_text_content(output_text)

    is_approved = "REJECTED" not in output_text.upper()
    duration = round(time.perf_counter() - start_time, 3)
    print(f" -> Compliance Agent Result ({duration}s): {output_text.strip()}")
    
    return {
        "compliance_assessment": output_text,
        "is_compliance_approved": is_approved
    }


@traceable(name="node_underwriter_decision", run_type="chain")
def node_underwriter_decision(state: ApplicationState) -> ApplicationState:
    """Node 3: Final Underwriter Decision Aggregator Node"""
    start_time = time.perf_counter()
    print("\n[WORKFLOW NODE 3]: Final Underwriting Decision Node...")
    
    fin_ok = state.get("is_financial_approved", False)
    comp_ok = state.get("is_compliance_approved", False)
    
    if fin_ok and comp_ok:
        decision = "CARD APPROVED: Credit card issued successfully."
    elif not fin_ok:
        decision = f"CARD REJECTED: Financial Risk Check Failed ({state.get('financial_assessment')})"
    else:
        decision = f"CARD REJECTED: Compliance Check Failed ({state.get('compliance_assessment')})"
        
    duration = round(time.perf_counter() - start_time, 3)
    print(f" -> Final Decision ({duration}s): {decision}")
    return {"final_decision": decision}


@traceable(name="node_notification_engine", run_type="chain")
def node_notification_engine(state: ApplicationState) -> ApplicationState:
    """Node 4: Customer Notification Node"""
    start_time = time.perf_counter()
    print("\n[WORKFLOW NODE 4]: Customer Notification Engine running...")
    name = state["applicant_name"]
    decision = state.get("final_decision", "REJECTED")
    log_msg = f"SMS/Email notification delivered to {name.upper()}: {decision}"
    duration = round(time.perf_counter() - start_time, 3)
    print(f" -> {log_msg} ({duration}s)")
    return {"notification_log": log_msg}


# ==========================================
# 4. AUTONOMOUS CONDITIONAL ROUTER (INSTRUMENTED)
# ==========================================
@traceable(name="route_after_financial", run_type="chain")
def route_after_financial(state: ApplicationState) -> Literal["compliance_node", "decision_node"]:
    """
    Autonomous Conditional Edge:
    If Financial Assessment fails, skip Compliance and route directly to Decision Node.
    If Financial Assessment passes, proceed to Compliance Node.
    """
    print("\n[AUTONOMOUS ROUTER]: Evaluating state after Financial Assessment...")
    if not state.get("is_financial_approved", False):
        print(" -> Financial Risk Failed! Short-circuiting workflow directly to Final Decision.")
        return "decision_node"
    else:
        print(" -> Financial Risk Passed! Routing to Compliance & KYC Agent.")
        return "compliance_node"


# ==========================================
# 5. WORKFLOW GRAPH ORCHESTRATION BUILDER
# ==========================================
def build_agentic_workflow():
    builder = StateGraph(ApplicationState)

    # Add Nodes
    builder.add_node("financial_node", node_financial_agent)
    builder.add_node("compliance_node", node_compliance_agent)
    builder.add_node("decision_node", node_underwriter_decision)
    builder.add_node("notification_node", node_notification_engine)

    # Add Edges & Dynamic Conditional Routing
    builder.add_edge(START, "financial_node")
    
    # Conditional Branching from Financial Node
    builder.add_conditional_edges("financial_node", route_after_financial)
    
    # Sequential Edges
    builder.add_edge("compliance_node", "decision_node")
    builder.add_edge("decision_node", "notification_node")
    builder.add_edge("notification_node", END)

    # Compile Executable Graph Workflow
    return builder.compile()


# ==========================================
# 6. RUN DEMO WORKFLOWS WITH OBSERVABILITY TRACING
# ==========================================
def main():
    print("==================================================")
    print("--- AUTONOMOUS AGENTIC AI WORKFLOW ORCHESTRATION ---")
    print("==================================================")

    # Initialize Observability status
    setup_observability()

    workflow_app = build_agentic_workflow()

    # TEST CASE 1: Eligible Applicant (Ayush)
    print("\n\n>>> RUNNING TEST CASE 1: Eligible Applicant (Ayush)")
    applicant_1: ApplicationState = {
        "applicant_name": "Ayush",
        "customer_id": "ID-889900",
        "income": 65000.0,
        "credit_score": 720,
        "loan_amount": 4000.0,
        "employment_type": "Salaried",
        "financial_assessment": "",
        "is_financial_approved": False,
        "compliance_assessment": "",
        "is_compliance_approved": False,
        "final_decision": "",
        "notification_log": ""
    }
    
    # Generate LangSmith observability configuration (tags & metadata)
    config_1 = get_observability_config(applicant_1, run_name="Run-1-Eligible-Ayush")
    
    start_total = time.perf_counter()
    result_1 = workflow_app.invoke(applicant_1, config=config_1)
    total_time_1 = round(time.perf_counter() - start_total, 2)
    
    print(f"\n[SUMMARY 1]: Final Outcome = {result_1['final_decision']} (Total Time: {total_time_1}s)")

    # TEST CASE 2: Ineligible Applicant (Low Credit Score -> Triggers Autonomous Short-Circuit Routing)
    print("\n\n" + "="*50)
    print(">>> RUNNING TEST CASE 2: Ineligible Applicant (Low Credit Score)")
    print("="*50)
    applicant_2: ApplicationState = {
        "applicant_name": "Rahul",
        "customer_id": "ID-112233",
        "income": 40000.0,
        "credit_score": 520,  # Below 600 -> Will trigger autonomous skip of Compliance Node
        "loan_amount": 2000.0,
        "employment_type": "Salaried",
        "financial_assessment": "",
        "is_financial_approved": False,
        "compliance_assessment": "",
        "is_compliance_approved": False,
        "final_decision": "",
        "notification_log": ""
    }
    
    # Generate LangSmith observability configuration (tags & metadata)
    config_2 = get_observability_config(applicant_2, run_name="Run-2-ShortCircuit-Rahul")
    
    start_total = time.perf_counter()
    result_2 = workflow_app.invoke(applicant_2, config=config_2)
    total_time_2 = round(time.perf_counter() - start_total, 2)
    
    print(f"\n[SUMMARY 2]: Final Outcome = {result_2['final_decision']} (Total Time: {total_time_2}s)")

if __name__ == "__main__":
    main()
