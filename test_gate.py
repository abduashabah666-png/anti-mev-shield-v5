from app import assess, evaluate_gate


def normal_assessment():
    return assess(
        deviation=0.2,
        slippage=0.5,
        sensitivity=0.1,
    )


def test_pass_when_all_values_are_within_limits():
    result = evaluate_gate(
        assessment=normal_assessment(),
        slippage=0.5,
        deviation=0.2,
        output=240.0,
        minimum=239.0,
        max_allowed_score=24,
        max_allowed_slippage=0.5,
        max_allowed_deviation=1.0,
    )

    assert result["status"] == "PASS (analysis gate only)"
    assert result["reasons"] == []


def test_block_when_slippage_exceeds_limit():
    result = evaluate_gate(
        assessment=normal_assessment(),
        slippage=0.5,
        deviation=0.2,
        output=240.0,
        minimum=239.0,
        max_allowed_slippage=0.1,
    )

    assert result["status"] == "BLOCK"
    assert any("Slippage" in reason for reason in result["reasons"])


def test_block_when_deviation_exceeds_limit():
    result = evaluate_gate(
        assessment=normal_assessment(),
        slippage=0.5,
        deviation=2.0,
        output=240.0,
        minimum=239.0,
        max_allowed_deviation=1.0,
    )

    assert result["status"] == "BLOCK"
    assert any("reference deviation" in reason for reason in result["reasons"])


def test_block_when_score_exceeds_limit():
    assessment = assess(
        deviation=5.0,
        slippage=0.5,
        sensitivity=0.1,
    )

    result = evaluate_gate(
        assessment=assessment,
        slippage=0.5,
        deviation=5.0,
        output=240.0,
        minimum=239.0,
        max_allowed_score=24,
        max_allowed_slippage=0.5,
        max_allowed_deviation=10.0,
    )

    assert result["status"] == "BLOCK"
    assert any("Heuristic score" in reason for reason in result["reasons"])
