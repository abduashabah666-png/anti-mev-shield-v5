"""Pure logic for the Anti-MEV Shield read-only analysis gate."""
from __future__ import annotations
import math
from numbers import Real
from typing import Any


def _finite_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, Real):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) else None


def assess(deviation: Any, slippage: Any, sensitivity: Any) -> dict:
    """Explainable heuristic assessment; not verified MEV attack detection."""
    dev, slip, sens = map(_finite_number, (deviation, slippage, sensitivity))
    missing = [name for name, value in (
        ("deviation", dev), ("slippage", slip), ("sensitivity", sens)
    ) if value is None]
    if missing:
        return {
            "status": "insufficient_data",
            "score": None,
            "reasons": [f"Missing or invalid numeric data: {', '.join(missing)}."],
            "warning": "Assessment unavailable; do not treat this as a safe quote.",
        }

    score, reasons = 0, []
    if abs(dev) >= 1.0:
        score += 40
        reasons.append("Price deviation is high (absolute deviation >= 1%).")
    elif abs(dev) >= 0.5:
        score += 20
        reasons.append("Price deviation is elevated (absolute deviation >= 0.5%).")
    if slip >= 1.0:
        score += 30
        reasons.append("Configured slippage is high (>= 1%).")
    elif slip >= 0.5:
        score += 15
        reasons.append("Configured slippage is elevated (>= 0.5%).")
    if sens >= 1.0:
        score += 30
        reasons.append("Quote-size sensitivity is high (>= 1%).")
    elif sens >= 0.5:
        score += 15
        reasons.append("Quote-size sensitivity is elevated (>= 0.5%).")
    if not reasons:
        reasons.append("No elevated heuristic indicators detected in the supplied values.")
    return {
        "status": "assessed",
        "score": min(score, 100),
        "reasons": reasons,
        "warning": "Heuristic indicators only; this is not verified MEV detection.",
    }


def evaluate_gate(
    assessment: Any, slippage: Any, deviation: Any, output: Any, minimum: Any,
    max_allowed_score: Any, max_allowed_slippage: Any, max_allowed_deviation: Any,
) -> dict:
    """Validate gate inputs and return PASS/BLOCK for analysis only."""
    reasons = []
    slip, dev, out_value, min_value, max_score, max_slip, max_dev = map(
        _finite_number,
        (slippage, deviation, output, minimum, max_allowed_score,
         max_allowed_slippage, max_allowed_deviation),
    )

    if not isinstance(assessment, dict):
        assessment = {}
        reasons.append("Assessment data is missing or invalid.")
    status = assessment.get("status")
    score = _finite_number(assessment.get("score"))
    if status == "insufficient_data" or score is None:
        reasons.append("Assessment is incomplete or contains invalid data.")
    elif status not in ("assessed", "ok", "success"):
        reasons.append("Assessment status is not recognized.")

    if slip is None:
        reasons.append("Slippage is missing or not a finite number.")
    elif slip < 0:
        reasons.append("Slippage cannot be negative.")
    if dev is None:
        reasons.append("Deviation is missing or not a finite number.")
    if out_value is None:
        reasons.append("Estimated output is missing or not a finite number.")
    elif out_value <= 0:
        reasons.append("Estimated output must be greater than zero.")
    if min_value is None:
        reasons.append("Minimum output is missing or not a finite number.")
    elif min_value <= 0:
        reasons.append("Minimum output must be greater than zero.")

    if max_score is None or not 0 <= max_score <= 100:
        reasons.append("Maximum allowed score must be finite and between 0 and 100.")
    if max_slip is None or max_slip < 0:
        reasons.append("Maximum allowed slippage must be finite and non-negative.")
    if max_dev is None or max_dev < 0:
        reasons.append("Maximum allowed absolute deviation must be finite and non-negative.")

    if score is not None:
        if not 0 <= score <= 100:
            reasons.append("Assessment score must be between 0 and 100.")
        elif max_score is not None and 0 <= max_score <= 100 and score > max_score:
            reasons.append(f"Risk score {score:g} exceeds the allowed maximum {max_score:g}.")
    if slip is not None and slip >= 0 and max_slip is not None and max_slip >= 0:
        if slip > max_slip:
            reasons.append(f"Slippage {slip:g}% exceeds the allowed maximum {max_slip:g}%.")
    if dev is not None and max_dev is not None and max_dev >= 0:
        if abs(dev) > max_dev:
            reasons.append(
                f"Absolute deviation {abs(dev):g}% exceeds the allowed maximum {max_dev:g}%."
            )
    if out_value is not None and min_value is not None and min_value > out_value:
        reasons.append("Minimum output exceeds estimated output; quote data is inconsistent.")

    blocked = bool(reasons)
    return {
        "status": "BLOCK" if blocked else "PASS (analysis gate only)",
        "reasons": reasons or ["All configured analysis-gate checks passed."],
        "execution_performed": False,
        "does_not_block_onchain_transactions": True,
        "warning": (
            "Read-only analysis gate: it does not submit, cancel, or block transactions "
            "on-chain and does not guarantee MEV prevention."
        ),
    }
