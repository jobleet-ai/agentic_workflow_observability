"""
Agentic AI Workflow Evaluation Module
-------------------------------------
Programmatically evaluates LangGraph workflow executions against Ground Truth datasets.

Evaluates:
1. Decision Accuracy (Expected vs Actual Approval/Rejection).
2. Short-Circuit Routing Efficiency (Did low credit score skip Compliance Node?).
3. Execution Latency (seconds per run).
4. Tool Call Execution Count.
"""

import time
import asyncio
import sys
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass

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

@dataclass
class TestCase:
    test_id: str
    applicant_name: str
    customer_id: str
    income: float
    credit_score: int
    loan_amount: float
    employment_type: str
    expected_decision: str  # 'APPROVED' or 'REJECTED'
    expected_compliance_skipped: bool  # True if short-circuit should occur


@dataclass
class EvalResult:
    test_id: str
    applicant_name: str
    actual_decision: str
    decision_matches_expected: bool
    compliance_skipped_correctly: bool
    latency_seconds: float
    status: str


# Dataset of Ground Truth Evaluation Test Cases
EVAL_DATASET: List[TestCase] = [
    TestCase(
        test_id="TC-001",
        applicant_name="Ayush",
        customer_id="ID-998811",
        income=65000.0,
        credit_score=720,
        loan_amount=4000.0,
        employment_type="Salaried",
        expected_decision="APPROVED",
        expected_compliance_skipped=False
    ),
    TestCase(
        test_id="TC-002",
        applicant_name="Rahul",
        customer_id="ID-112233",
        income=40000.0,
        credit_score=520,  # Credit score < 600 -> Should REJECT & skip Compliance
        loan_amount=2000.0,
        employment_type="Salaried",
        expected_decision="REJECTED",
        expected_compliance_skipped=True
    ),
    TestCase(
        test_id="TC-003",
        applicant_name="Priya",
        customer_id="ID-445566",
        income=25000.0,  # Income < 30000 -> Should REJECT & skip Compliance
        credit_score=750,
        loan_amount=3000.0,
        employment_type="Salaried",
        expected_decision="REJECTED",
        expected_compliance_skipped=True
    ),
    TestCase(
        test_id="TC-004",
        applicant_name="Vikram",
        customer_id="ID-778899",
        income=80000.0,
        credit_score=710,
        loan_amount=5000.0,
        employment_type="Freelance",  # Invalid employment -> Fails Compliance node
        expected_decision="REJECTED",
        expected_compliance_skipped=False
    )
]


async def evaluate_workflow() -> Dict:
    print("==================================================")
    print("--- AGENTIC WORKFLOW EVALUATION BENCHMARK ---")
    print("==================================================\n")

    workflow_app = build_agentic_workflow()
    eval_results: List[EvalResult] = []

    total_latency = 0.0
    correct_decisions = 0
    correct_routing = 0

    for tc in EVAL_DATASET:
        print(f"Running Eval for [{tc.test_id}] - {tc.applicant_name} (Score: {tc.credit_score}, Income: ${tc.income})...")
        
        initial_state: ApplicationState = {
            "applicant_name": tc.applicant_name,
            "customer_id": tc.customer_id,
            "income": tc.income,
            "credit_score": tc.credit_score,
            "loan_amount": tc.loan_amount,
            "employment_type": tc.employment_type,
            "financial_assessment": "",
            "is_financial_approved": False,
            "compliance_assessment": "",
            "is_compliance_approved": False,
            "final_decision": "",
            "notification_log": ""
        }

        obs_config = get_observability_config(initial_state, run_name=f"Eval-{tc.test_id}-{tc.applicant_name}")
        start_time = time.perf_counter()
        final_state = await workflow_app.ainvoke(initial_state, config=obs_config)
        latency = round(time.perf_counter() - start_time, 2)
        total_latency += latency

        # Evaluate Metrics
        actual_decision = final_state.get("final_decision", "")
        is_approved_actual = "APPROVED" in actual_decision
        is_approved_expected = tc.expected_decision == "APPROVED"
        decision_match = (is_approved_actual == is_approved_expected)
        
        # Evaluate Compliance Node Skipping (Short-circuit metric)
        compliance_text = final_state.get("compliance_assessment", "")
        was_compliance_skipped = (compliance_text == "")
        routing_match = (was_compliance_skipped == tc.expected_compliance_skipped)

        if decision_match:
            correct_decisions += 1
        if routing_match:
            correct_routing += 1

        eval_results.append(EvalResult(
            test_id=tc.test_id,
            applicant_name=tc.applicant_name,
            actual_decision="APPROVED" if is_approved_actual else "REJECTED",
            decision_matches_expected=decision_match,
            compliance_skipped_correctly=routing_match,
            latency_seconds=latency,
            status="PASSED" if (decision_match and routing_match) else "FAILED"
        ))

    # Calculate Aggregate Metrics
    n_tests = len(EVAL_DATASET)
    decision_accuracy = (correct_decisions / n_tests) * 100
    routing_accuracy = (correct_routing / n_tests) * 100
    avg_latency = round(total_latency / n_tests, 2)

    print("\n" + "="*50)
    print("--- EVALUATION BENCHMARK SUMMARY REPORT ---")
    print("="*50)
    print(f"Total Test Cases Evaluated   : {n_tests}")
    print(f"Underwriting Decision Accuracy: {decision_accuracy:.1f}%")
    print(f"Short-Circuit Router Accuracy : {routing_accuracy:.1f}%")
    print(f"Average Execution Latency    : {avg_latency} seconds/run")
    print("="*50 + "\n")

    for res in eval_results:
        print(f"[{res.test_id}] {res.applicant_name:<10} | Result: {res.actual_decision:<8} | Decision Match: {res.decision_matches_expected} | Routing Match: {res.compliance_skipped_correctly} | Latency: {res.latency_seconds}s | Status: {res.status}")

    return {
        "decision_accuracy_pct": decision_accuracy,
        "routing_accuracy_pct": routing_accuracy,
        "avg_latency_sec": avg_latency,
        "results": eval_results
    }


if __name__ == "__main__":
    asyncio.run(evaluate_workflow())
