import json
import logging
import os
from datetime import timedelta

import azure.functions as func
import azure.durable_functions as df

app = df.DFApp(http_auth_level=func.AuthLevel.ANONYMOUS)

VALID_CATEGORIES = {"travel", "meals", "supplies", "equipment", "software", "other"}


def _safe_json_response(payload: dict, status_code: int = 200) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps(payload, indent=2),
        status_code=status_code,
        mimetype="application/json"
    )


# ---------------------------------------------------------
# 1) HTTP starter: starts the orchestration
# ---------------------------------------------------------
@app.route(route="expenses/start", methods=["POST"])
@app.durable_client_input(client_name="client")
async def start_expense_workflow(req: func.HttpRequest, client):
    try:
        body = req.get_json()
    except ValueError:
        return _safe_json_response(
            {
                "error": "Invalid JSON request body."
            },
            status_code=400
        )

    instance_id = await client.start_new("expense_approval_orchestrator", None, body)
    logging.info(f"Started orchestration with ID = '{instance_id}'.")

    return client.create_check_status_response(req, instance_id)


# ---------------------------------------------------------
# 2) Orchestrator: main workflow
# ---------------------------------------------------------
@app.orchestration_trigger(context_name="context")
def expense_approval_orchestrator(context: df.DurableOrchestrationContext):
    expense = context.get_input()

    # Step 1: Validate
    validation_result = yield context.call_activity("validate_expense_activity", expense)

    if not validation_result["is_valid"]:
        final_result = {
            "status": "validation_error",
            "reason": validation_result["reason"],
            "expense": expense,
            "manager_required": False,
            "escalated": False
        }

        yield context.call_activity("notify_employee_activity", final_result)
        return final_result

    amount = float(expense["amount"])

    # Step 2: Auto-approve if under 100
    if amount < 100:
        final_result = {
            "status": "approved",
            "reason": "Auto-approved because amount is under $100.",
            "expense": expense,
            "manager_required": False,
            "escalated": False
        }

        yield context.call_activity("notify_employee_activity", final_result)
        return final_result

    # Step 3: Manager approval required
    timeout_minutes = int(os.getenv("MANAGER_TIMEOUT_MINUTES", "2"))
    deadline = context.current_utc_datetime + timedelta(minutes=timeout_minutes)

    approval_event = context.wait_for_external_event("ManagerDecision")
    timeout_task = context.create_timer(deadline)

    winner = yield context.task_any([approval_event, timeout_task])

    if winner == approval_event:
        manager_decision = approval_event.result

        if str(manager_decision).lower() == "approve":
            final_result = {
                "status": "approved",
                "reason": "Approved by manager.",
                "expense": expense,
                "manager_required": True,
                "escalated": False
            }
        else:
            final_result = {
                "status": "rejected",
                "reason": "Rejected by manager.",
                "expense": expense,
                "manager_required": True,
                "escalated": False
            }
    else:
        final_result = {
            "status": "escalated",
            "reason": "No manager response before timeout. Auto-approved and flagged as escalated.",
            "expense": expense,
            "manager_required": True,
            "escalated": True
        }

    yield context.call_activity("notify_employee_activity", final_result)
    return final_result


# ---------------------------------------------------------
# 3) Validation activity
# ---------------------------------------------------------
@app.activity_trigger(input_name="expense")
def validate_expense_activity(expense: dict) -> dict:
    required_fields = [
        "employee_name",
        "employee_email",
        "amount",
        "category",
        "description",
        "manager_email"
    ]

    if not isinstance(expense, dict):
        return {
            "is_valid": False,
            "reason": "Request body must be a JSON object."
        }

    missing_fields = []
    for field in required_fields:
        value = expense.get(field)
        if value is None or str(value).strip() == "":
            missing_fields.append(field)

    if missing_fields:
        return {
            "is_valid": False,
            "reason": f"Missing required fields: {', '.join(missing_fields)}"
        }

    try:
        amount = float(expense["amount"])
        if amount < 0:
            return {
                "is_valid": False,
                "reason": "Amount must be 0 or greater."
            }
    except (TypeError, ValueError):
        return {
            "is_valid": False,
            "reason": "Amount must be a valid number."
        }

    category = str(expense["category"]).strip().lower()
    if category not in VALID_CATEGORIES:
        return {
            "is_valid": False,
            "reason": (
                "Invalid category. Valid categories are: "
                "travel, meals, supplies, equipment, software, other."
            )
        }

    return {
        "is_valid": True,
        "reason": "Validation passed."
    }


# ---------------------------------------------------------
# 4) Notification activity
# For now this logs the final result.
# This is enough for demo/testing and can be upgraded later.
# ---------------------------------------------------------
@app.activity_trigger(input_name="final_result")
def notify_employee_activity(final_result: dict) -> dict:
    expense = final_result.get("expense", {})
    employee_email = expense.get("employee_email", "unknown@example.com")
    employee_name = expense.get("employee_name", "Unknown Employee")

    message = {
        "to": employee_email,
        "subject": f"Expense Request Result: {final_result['status'].upper()}",
        "body": (
            f"Hello {employee_name}, your expense request has been processed.\n"
            f"Final status: {final_result['status']}\n"
            f"Reason: {final_result['reason']}\n"
            f"Escalated: {final_result.get('escalated', False)}"
        )
    }

    logging.info("=== EMPLOYEE NOTIFICATION ===")
    logging.info(json.dumps(message, indent=2))
    logging.info("=== END NOTIFICATION ===")

    return {
        "notification_sent": True,
        "channel": "log",
        "to": employee_email
    }


# ---------------------------------------------------------
# 5) HTTP endpoint for manager decision
# Usage:
# POST /api/expenses/{instanceId}/decision
# body: { "decision": "approve" }
# or   { "decision": "reject" }
# ---------------------------------------------------------
@app.route(route="expenses/{instanceId}/decision", methods=["POST"])
@app.durable_client_input(client_name="client")
async def manager_decision(req: func.HttpRequest, client):
    instance_id = req.route_params.get("instanceId")

    if not instance_id:
        return _safe_json_response(
            {"error": "instanceId route parameter is required."},
            status_code=400
        )

    try:
        body = req.get_json()
    except ValueError:
        return _safe_json_response(
            {"error": "Invalid JSON request body."},
            status_code=400
        )

    decision = str(body.get("decision", "")).strip().lower()
    if decision not in {"approve", "reject"}:
        return _safe_json_response(
            {"error": "Decision must be either 'approve' or 'reject'."},
            status_code=400
        )

    await client.raise_event(instance_id, "ManagerDecision", decision)

    return _safe_json_response(
        {
            "message": f"Manager decision '{decision}' sent successfully.",
            "instanceId": instance_id
        },
        status_code=200
    )


# ---------------------------------------------------------
# 6) Friendly status endpoint
# Optional helper to view current orchestration status as JSON
# ---------------------------------------------------------
@app.route(route="expenses/{instanceId}/status", methods=["GET"])
@app.durable_client_input(client_name="client")
async def get_status(req: func.HttpRequest, client):
    instance_id = req.route_params.get("instanceId")

    if not instance_id:
        return _safe_json_response(
            {"error": "instanceId route parameter is required."},
            status_code=400
        )

    status = await client.get_status(instance_id)

    if not status:
        return _safe_json_response(
            {"error": "No orchestration found for the given instanceId."},
            status_code=404
        )

    return _safe_json_response(status.to_json())