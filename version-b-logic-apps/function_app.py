import json
import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

VALID_CATEGORIES = {"travel", "meals", "supplies", "equipment", "software", "other"}


def json_response(payload, status_code=200):
    return func.HttpResponse(
        json.dumps(payload, indent=2),
        status_code=status_code,
        mimetype="application/json"
    )


@app.route(route="validate-expense", methods=["POST"])
def validate_expense(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
    except ValueError:
        return json_response({
            "is_valid": False,
            "reason": "Invalid JSON body."
        }, 400)

    required_fields = [
        "employee_name",
        "employee_email",
        "amount",
        "category",
        "description",
        "manager_email"
    ]

    missing_fields = []
    for field in required_fields:
        value = body.get(field)
        if value is None or str(value).strip() == "":
            missing_fields.append(field)

    if missing_fields:
        return json_response({
            "is_valid": False,
            "reason": f"Missing required fields: {', '.join(missing_fields)}"
        })

    try:
        amount = float(body["amount"])
        if amount < 0:
            return json_response({
                "is_valid": False,
                "reason": "Amount must be 0 or greater."
            })
    except (TypeError, ValueError):
        return json_response({
            "is_valid": False,
            "reason": "Amount must be a valid number."
        })

    category = str(body["category"]).strip().lower()
    if category not in VALID_CATEGORIES:
        return json_response({
            "is_valid": False,
            "reason": "Invalid category. Valid categories are: travel, meals, supplies, equipment, software, other."
        })

    return json_response({
        "is_valid": True,
        "reason": "Validation passed."
    })