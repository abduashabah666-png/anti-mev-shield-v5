def assess(deviation, slippage, sensitivity):
    """Transparent heuristic only; not verified attack detection."""
    missing = []

    if deviation is None:
        missing.append("External reference deviation is unavailable.")

    if sensitivity is None:
        missing.append("Quote-size sensitivity is unavailable.")

    score = 0
    reasons = []

    if deviation is not None:
        magnitude = abs(float(deviation))

        if magnitude >= 5:
            score += 45
            reasons.append(
                "Quote differs from the reference snapshot by at least 5%."
            )
        elif magnitude >= 2:
            score += 25
            reasons.append(
                "Quote differs from the reference snapshot by at least 2%."
            )
        elif magnitude >= 1:
            score += 10
            reasons.append(
                "Quote differs from the reference snapshot by at least 1%."
            )
        else:
            reasons.append(
                "Quote deviation from the reference snapshot is below 1%."
            )

    if slippage >= 3:
        score += 25
        reasons.append("Selected slippage tolerance is 3% or more.")
    elif slippage >= 1:
        score += 12
        reasons.append("Selected slippage tolerance is at least 1%.")
    else:
        reasons.append("Selected slippage tolerance is below 1%.")

    if sensitivity is not None:
        magnitude = abs(float(sensitivity))

        if magnitude >= 5:
            score += 25
            reasons.append(
                "Output-per-input varies by at least 5% across probes."
            )
        elif magnitude >= 2:
            score += 15
            reasons.append(
                "Output-per-input varies by at least 2% across probes."
            )
        elif magnitude >= 1:
            score += 8
            reasons.append(
                "Output-per-input varies by at least 1% across probes."
            )
        else:
            reasons.append(
                "Quote-size sensitivity is below 1% across tested probes."
            )

    score = min(score, 100)

    if missing:
        label = "Insufficient data"
        status = "insufficient_data"
    else:
        label = (
            "High indicator level"
            if score >= 50
            else "Moderate indicator level"
            if score >= 25
            else "Lower indicator level"
        )
        status = "indicators_available"

    return {
        "score_out_of_100": score,
        "label": label,
        "status": status,
        "missing_data": missing,
        "reasons": reasons,
        "verified_attack_detection": False,
        "warning": (
            "Heuristic indicators only. This score does not confirm "
            "an attack or prove MEV prevention."
        ),
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
    """Application-level gate only; does not submit or block transactions."""
    reasons = []

    if assessment.get("status") != "indicators_available":
        reasons.append("Required analysis data is missing.")

    score = assessment.get("score_out_of_100")

    if score is None:
        reasons.append("Heuristic score is unavailable.")
    elif score > max_allowed_score:
        reasons.append(
            f"Heuristic score {score} exceeds configured maximum "
            f"{max_allowed_score}."
        )

    if slippage is None:
        reasons.append("Slippage value is unavailable.")
    elif slippage > max_allowed_slippage:
        reasons.append(
            f"Slippage {slippage:.2f}% exceeds configured maximum "
            f"{max_allowed_slippage:.2f}%."
        )

    if deviation is None:
        reasons.append("Reference-price deviation is unavailable.")
    elif abs(deviation) > max_allowed_deviation:
        reasons.append(
            f"Absolute reference deviation {abs(deviation):.3f}% "
            f"exceeds configured maximum {max_allowed_deviation:.2f}%."
        )

    try:
        if (
            output is None
            or minimum is None
            or output <= 0
            or minimum <= 0
        ):
            reasons.append("Quote output or minimum output is not positive.")
    except (TypeError, ValueError):
        reasons.append(
            "Quote output or minimum output is unavailable or invalid."
        )

    return {
        "status": "BLOCK" if reasons else "PASS (analysis gate only)",
        "reasons": reasons,
        "execution_performed": False,
        "does_not_block_onchain_transactions": True,
    }
