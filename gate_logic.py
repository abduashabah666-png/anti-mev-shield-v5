"""Anti-MEV Shield V5.1 gate logic.
Read-only application analysis; it does not sign, submit, or block on-chain transactions.
The score is a heuristic, not verified MEV detection or an attack probability.
"""
from math import isfinite


def _finite_number(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if isfinite(number) else None


def assess(deviation, slippage, sensitivity):
    values = {
        "deviation": _finite_number(deviation),
        "slippage": _finite_number(slippage),
        "sensitivity": _finite_number(sensitivity),
    }
    names = {
        "deviation": "reference deviation",
        "slippage": "slippage",
        "sensitivity": "quote-size sensitivity",
    }
    missing = [key for key, value in values.items() if value is None]
    warning = (
        "Heuristic indicator only; not verified MEV detection, not an attack "
        "probability, and not a guarantee of prevention."
    )
    if missing:
        return {
            "status": "insufficient_data",
            "score": None,
            "score_out_of_100": None,
            "label": "Insufficient data",
            "reasons": ["Required analysis data is missing: " +
                        ", ".join(names[key] for key in missing)],
            "missing_data": [names[key] for key in missing],
            "warning": warning,
        }

    if values["slippage"] < 0 or values["sensitivity"] < 0:
        invalid = [names[key] for key in ("slippage", "sensitivity")
                   if values[key] < 0]
        return {
            "status": "insufficient_data",
            "score": None,
            "score_out_of_100": None,
            "label": "Invalid input",
            "reasons": ["Values must not be negative: " + ", ".join(invalid)],
            "missing_data": [],
            "warning": warning,
        }

    score = int(round(min(
        100.0,
        abs(values["deviation"]) * 10.0
        + values["slippage"] * 4.0
        + values["sensitivity"] * 10.0,
    )))
    reasons = []
    if abs(values["deviation"]) > 1.0:
        reasons.append("Absolute reference-price deviation exceeds 1%.")
    if values["slippage"] > 0.5:
        reasons.append("Configured slippage tolerance exceeds 0.5%.")
    if values["sensitivity"] > 1.0:
        reasons.append("Quote-size sensitivity exceeds 1%.")
    if not reasons:
        reasons.append("No elevated heuristic indicator was found in this snapshot.")

    label = ("Elevated indicators" if score >= 50 else
             "Moderate indicators" if score >= 25 else "Lower indicators")
    return {
        "status": "indicators_available",
        "score": score,
        "score_out_of_100": score,
        "label": label,
        "reasons": reasons,
        "missing_data": [],
        "warning": warning,
    }


def evaluate_gate(
    assessment, slippage, deviation, output, minimum,
    max_allowed_score=24, max_allowed_slippage=0.5,
    max_allowed_deviation=1.0,
):
    reasons = []
    slip = _finite_number(slippage)
    dev = _finite_number(deviation)
    out = _finite_number(output)
    min_out = _finite_number(minimum)
    score_limit = _finite_number(max_allowed_score)
    slip_limit = _finite_number(max_allowed_slippage)
    dev_limit = _finite_number(max_allowed_deviation)

    if not isinstance(assessment, dict):
        reasons.append("Required analysis data is missing.")
        score = None
    else:
        if assessment.get("status") == "insufficient_data":
            reasons.append("Assessment reports insufficient or invalid data.")
        score = _finite_number(
            assessment.get("score_out_of_100", assessment.get("score"))
        )

    if score is None:
        reasons.append("Heuristic score is missing or invalid.")
    elif score_limit is None or score_limit < 0:
        reasons.append("Maximum allowed score must be a finite non-negative number.")
    elif score > score_limit:
        reasons.append("Heuristic score exceeds the configured limit.")

    if slip is None or slip < 0:
        reasons.append("Slippage must be a finite non-negative number.")
    elif slip_limit is None or slip_limit < 0:
        reasons.append("Maximum allowed slippage must be a finite non-negative number.")
    elif slip > slip_limit:
        reasons.append("Slippage exceeds the configured limit.")

    if dev is None:
        reasons.append("Reference deviation is missing or invalid.")
    elif dev_limit is None or dev_limit < 0:
        reasons.append("Maximum allowed deviation must be a finite non-negative number.")
    elif abs(dev) > dev_limit:
        reasons.append("Absolute reference deviation exceeds the configured limit.")

    if out is None:
        reasons.append("Output must be a finite number.")
    elif out <= 0:
        reasons.append("Output must be positive; output is zero or negative.")

    if min_out is None:
        reasons.append("Minimum output must be a finite number.")
    elif min_out <= 0:
        reasons.append("Minimum output must be positive; minimum output is zero or negative.")

    if out is not None and min_out is not None and out > 0 and min_out > out:
        reasons.append("Minimum output exceeds estimated output.")

    return {
        "status": "BLOCK" if reasons else "PASS (analysis gate only)",
        "reasons": reasons,
        "execution_performed": False,
        "does_not_block_onchain_transactions": True,
    }
