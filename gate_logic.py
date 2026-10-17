"""Compatibility layer for Anti-MEV Shield V5.1.
Application-level analysis only; does not execute or block on-chain transactions.
"""
from math import isfinite


def _number(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        n = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return n if isfinite(n) else None


def assess(deviation, slippage, sensitivity):
    values = {
        "reference deviation": _number(deviation),
        "slippage": _number(slippage),
        "quote-size sensitivity": _number(sensitivity),
    }
    missing = [name for name, value in values.items() if value is None]
    warning = (
        "Heuristic score only; it is not a probability, verified attack detection, "
        "or a guarantee of MEV prevention."
    )
    if missing:
        return {
            "status": "insufficient_data",
            "score": None,
            "score_out_of_100": None,
            "label": "Insufficient data",
            "reasons": ["Required analysis data is missing: " + ", ".join(missing)],
            "missing_data": missing,
            "warning": warning,
        }

    dev = abs(values["reference deviation"])
    slip = max(0.0, values["slippage"])
    sens = max(0.0, values["quote-size sensitivity"])
    score = int(round(min(100.0, dev * 10.0 + slip * 4.0 + sens * 10.0)))
    reasons = []
    if dev > 1.0:
        reasons.append("Reference-price deviation is elevated.")
    if slip > 0.5:
        reasons.append("Configured slippage tolerance is relatively high.")
    if sens > 1.0:
        reasons.append("Quote-size sensitivity is elevated.")
    if not reasons:
        reasons.append("No elevated heuristic indicator was detected in this snapshot.")
    label = "Elevated indicators" if score >= 50 else (
        "Moderate indicators" if score >= 25 else "Lower indicators"
    )
    return {
        "status": "indicators_available",
        "score": score,  # legacy key retained for existing tests
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
    slip = _number(slippage)
    dev = _number(deviation)
    out = _number(output)
    min_out = _number(minimum)
    max_score = _number(max_allowed_score)
    max_slip = _number(max_allowed_slippage)
    max_dev = _number(max_allowed_deviation)

    if not isinstance(assessment, dict) or assessment.get("status") == "insufficient_data":
        reasons.append("Required analysis data is missing.")
    score = _number(
        assessment.get("score_out_of_100", assessment.get("score"))
        if isinstance(assessment, dict) else None
    )
    if score is None:
        reasons.append("Heuristic score is missing or invalid.")
    elif max_score is None or score > max_score:
        reasons.append("Heuristic score exceeds the configured limit.")

    if slip is None or max_slip is None or slip < 0 or max_slip < 0:
        reasons.append("Slippage values must be finite non-negative numbers.")
    elif slip > max_slip:
        reasons.append("Slippage exceeds the configured limit.")

    if dev is None or max_dev is None or max_dev < 0:
        reasons.append("Required analysis data is missing: reference deviation.")
    elif abs(dev) > max_dev:
        reasons.append("Absolute reference deviation exceeds the configured limit.")

    if out is None or min_out is None:
        reasons.append("Output and minimum output must be finite numbers.")
    else:
        if out <= 0:
    reasons.append("Output must be positive; output is zero or negative.")

if min_out <= 0:
    reasons.append("Minimum output must be positive; minimum output is zero or negative.")
        if min_out > out:
            reasons.append("Minimum output exceeds estimated output.")

    return {
        "status": "BLOCK" if reasons else "PASS (analysis gate only)",
        "reasons": reasons,
        "execution_performed": False,
        "does_not_block_onchain_transactions": True,
    }
