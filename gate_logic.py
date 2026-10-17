"""Pure analysis and gate logic for Anti-MEV Shield."""
import math


def assess(deviation, slippage, sensitivity):
    """Heuristic indicators only; missing data is not treated as low risk."""
    missing = []
    reasons = []
    score = 0

    if deviation is None:
        missing.append("External reference deviation is unavailable.")
    else:
        try:
            magnitude = abs(float(deviation))
            if not math.isfinite(magnitude):
                missing.append("External reference deviation is invalid.")
            elif magnitude >= 5:
                score += 45
                reasons.append("Quote differs from the reference snapshot by at least 5%.")
            elif magnitude >= 2:
                score += 25
                reasons.append("Quote differs from the reference snapshot by at least 2%.")
            elif magnitude >= 1:
                score += 10
                reasons.append("Quote differs from the reference snapshot by at least 1%.")
            else:
                reasons.append("Quote deviation from the reference snapshot is below 1%.")
        except (TypeError, ValueError, OverflowError):
            missing.append("External reference deviation is invalid.")

    try:
        slip = float(slippage)
        if not math.isfinite(slip) or slip < 0:
            missing.append("Slippage value is invalid.")
            slip = None
    except (TypeError, ValueError, OverflowError):
        missing.append("Slippage value is unavailable or invalid.")
        slip = None

    if slip is not None:
        if slip >= 3:
            score += 25
            reasons.append("Selected slippage tolerance is 3% or more.")
        elif slip >= 1:
            score += 12
            reasons.append("Selected slippage tolerance is at least 1%.")
        else:
            reasons.append("Selected slippage tolerance is below 1%.")

    if sensitivity is None:
        missing.append("Quote-size sensitivity is unavailable.")
    else:
        try:
            magnitude = abs(float(sensitivity))
            if not math.isfinite(magnitude):
                missing.append("Quote-size sensitivity is invalid.")
            elif magnitude >= 5:
                score += 25
                reasons.append("Output-per-input varies by at least 5% across probes.")
            elif magnitude >= 2:
                score += 15
                reasons.append("Output-per-input varies by at least 2% across probes.")
            elif magnitude >= 1:
                score += 8
                reasons.append("Output-per-input varies by at least 1% across probes.")
            else:
                reasons.append("Quote-size sensitivity is below 1% across tested probes.")
        except (TypeError, ValueError, OverflowError):
            missing.append("Quote-size sensitivity is unavailable or invalid.")

    score = min(score, 100)
    if missing:
        label, status = "Insufficient data", "insufficient_data"
    else:
        label = "High indicator level" if score >= 50 else "Moderate indicator level" if score >= 25 else "Lower indicator level"
        status = "indicators_available"

    return {
        "score_out_of_100": score,
        "label": label,
        "status": status,
        "missing_data": missing,
        "reasons": reasons,
        "verified_attack_detection": False,
        "warning": "Heuristic indicators only. This score does not confirm an attack or prove MEV prevention.",
    }


def evaluate_gate(
    assessment,
    slippage,
    deviation,
    output,
    minimum,
    max_allowed_score=24,
    max_allowed_slippage=0.5,
    max_allowed_deviation=1.0,
):
    """Application-level gate only; it never submits or blocks blockchain transactions."""
    reasons = []

    if not isinstance(assessment, dict):
        assessment = {}
        reasons.append("Analysis assessment is unavailable or invalid.")

    if assessment.get("status") != "indicators_available":
        reasons.append("Required analysis data is missing.")

    try:
        score = assessment.get("score_out_of_100")
        if score is None or not math.isfinite(float(score)):
            reasons.append("Heuristic score is unavailable or invalid.")
        elif float(score) > float(max_allowed_score):
            reasons.append(f"Heuristic score {score} exceeds configured maximum {max_allowed_score}.")
    except (TypeError, ValueError, OverflowError):
        reasons.append("Heuristic score or configured maximum is invalid.")

    try:
        if slippage is None or not math.isfinite(float(slippage)):
            reasons.append("Slippage value is unavailable or invalid.")
        elif float(slippage) < 0:
            reasons.append("Slippage value cannot be negative.")
        elif float(slippage) > float(max_allowed_slippage):
            reasons.append(f"Slippage {float(slippage):.2f}% exceeds configured maximum {float(max_allowed_slippage):.2f}%.")
    except (TypeError, ValueError, OverflowError):
        reasons.append("Slippage value or configured maximum is invalid.")

    try:
        if deviation is None or not math.isfinite(float(deviation)):
            reasons.append("Reference-price deviation is unavailable or invalid.")
        elif abs(float(deviation)) > float(max_allowed_deviation):
            reasons.append(f"Absolute reference deviation {abs(float(deviation)):.3f}% exceeds configured maximum {float(max_allowed_deviation):.2f}%.")
    except (TypeError, ValueError, OverflowError):
        reasons.append("Reference-price deviation or configured maximum is invalid.")

    try:
        if output is None or minimum is None:
            reasons.append("Quote output or minimum output is unavailable.")
        else:
            out_value = float(output)
            min_value = float(minimum)
            if not math.isfinite(out_value) or not math.isfinite(min_value):
                reasons.append("Quote output or minimum output must be finite numbers.")
            elif out_value <= 0 or min_value <= 0:
                reasons.append("Quote output or minimum output is not positive.")
            elif min_value > out_value:
                reasons.append("Minimum output exceeds estimated output; quote data is inconsistent.")
    except (TypeError, ValueError, OverflowError):
        reasons.append("Quote output or minimum output is unavailable or invalid.")

    return {
        "status": "BLOCK" if reasons else "PASS (analysis gate only)",
        "reasons": reasons,
        "execution_performed": False,
        "does_not_block_onchain_transactions": True,
    }
