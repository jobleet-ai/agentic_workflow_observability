"""
Production REST API Server for Agentic Workflow
------------------------------------------------
Wraps the LangGraph Credit Card Agentic Workflow into a scalable FastAPI REST API.

Features:
1. Health Check Endpoint (/health) for Kubernetes / AWS ALB Liveness & Readiness probes.
2. Production Input Validation via Pydantic schemas.
3. Asynchronous Workflow Execution using LangGraph API (`ainvoke`).
4. API Key Header Security Validation.
"""

import os
import sys
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Header, Security, status
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Ensure root, src, and package directories are in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from src.agentic_workflow.agentic_workflow import build_agentic_workflow, get_observability_config, ApplicationState
except ModuleNotFoundError:
    try:
        from .agentic_workflow import build_agentic_workflow, get_observability_config, ApplicationState
    except ImportError:
        from agentic_workflow import build_agentic_workflow, get_observability_config, ApplicationState

load_dotenv()

# Initialize FastAPI App
app = FastAPI(
    title="Agentic AI Credit Card Processing Service",
    description="Production API for Autonomous Credit Card Approval Workflow powered by LangGraph & Gemini",
    version="1.0.0"
)

# Compile LangGraph Workflow instance
workflow_app = build_agentic_workflow()

# API Key Security Header (Optional Production Security Pattern)
API_KEY_NAME = "X-API-Key"
EXPECTED_API_KEY = os.getenv("API_SERVER_KEY", "prod-secret-key-123")

def verify_api_key(x_api_key: str = Header(..., alias=API_KEY_NAME)):
    if x_api_key != EXPECTED_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key header."
        )


# ==========================================
# PYDANTIC INPUT / OUTPUT SCHEMAS
# ==========================================
class CreditCardApplicationRequest(BaseModel):
    applicant_name: str = Field(..., example="Ayush Kumar", description="Full name of applicant")
    customer_id: str = Field(..., example="ID-998811", description="Unique customer ID or SSN")
    income: float = Field(..., example=65000.0, description="Annual gross income")
    credit_score: int = Field(..., example=720, description="FICO/Credit Score")
    loan_amount: float = Field(..., example=4000.0, description="Requested card limit or existing loan")
    employment_type: str = Field(..., example="Salaried", description="Salaried or Self-Employed")


class CreditCardApplicationResponse(BaseModel):
    status: str
    applicant_name: str
    customer_id: str
    financial_assessment: str
    is_financial_approved: bool
    compliance_assessment: Optional[str] = "Skipped due to early financial rejection"
    is_compliance_approved: Optional[str] = "Skipped"
    final_decision: str
    notification_log: str


# ==========================================
# ENDPOINTS
# ==========================================
@app.get("/health", status_code=200)
def health_check():
    """Health check for container orchestrators (Kubernetes / AWS ECS)."""
    return {
        "status": "healthy",
        "service": "agentic-credit-card-workflow",
        "engine": "LangGraph + Gemini"
    }


@app.post(
    "/api/v1/applications/process",
    response_model=CreditCardApplicationResponse,
    status_code=200
)
async def process_application(
    request: CreditCardApplicationRequest,
    # Uncomment next line to enforce API key security in production:
    # key: str = Security(verify_api_key)
):
    """
    Executes the autonomous agentic workflow for a customer application.
    """
    try:
        # Build initial state dictionary
        initial_state: ApplicationState = {
            "applicant_name": request.applicant_name,
            "customer_id": request.customer_id,
            "income": request.income,
            "credit_score": request.credit_score,
            "loan_amount": request.loan_amount,
            "employment_type": request.employment_type,
            "financial_assessment": "",
            "is_financial_approved": False,
            "compliance_assessment": "",
            "is_compliance_approved": False,
            "final_decision": "",
            "notification_log": ""
        }

        # Generate LangSmith Observability Config (Tags & Metadata)
        obs_config = get_observability_config(initial_state, run_name=f"API-Application-{request.applicant_name}")

        # Asynchronously invoke the LangGraph Agentic Workflow with Tracing
        final_state = await workflow_app.ainvoke(initial_state, config=obs_config)

        return CreditCardApplicationResponse(
            status="SUCCESS",
            applicant_name=final_state["applicant_name"],
            customer_id=final_state["customer_id"],
            financial_assessment=final_state.get("financial_assessment", ""),
            is_financial_approved=final_state.get("is_financial_approved", False),
            compliance_assessment=final_state.get("compliance_assessment", "Skipped due to early rejection"),
            is_compliance_approved=str(final_state.get("is_compliance_approved", "Skipped")),
            final_decision=final_state.get("final_decision", ""),
            notification_log=final_state.get("notification_log", "")
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing agentic workflow: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
