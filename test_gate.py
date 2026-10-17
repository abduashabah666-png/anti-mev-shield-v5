import pytest
from gate_logic import assess, evaluate_gate


def good_assessment(score=10):
    return {"status": "assessed", "score": score, "reasons": []}


def run_gate(**overrides):
    values = dict(
        assessment=good_assessment(), slippage=0.2, deviation=0.1,
        output=100.0, minimum=99.0, max_allowed_score=50,
        max_allowed_slippage=0.5, max_allowed_deviation=1.0,
    )
    values.update(overrides)
    return evaluate_gate(**values)


def test_pass_within_limits():
    result = run_gate()
    assert result["status"] == "PASS (analysis gate only)"
    assert result["execution_performed"] is False
    assert result["does_not_block_onchain_transactions"] is True


@pytest.mark.parametrize("field,value", [
    ("slippage", -0.1), ("max_allowed_score", -1), ("max_allowed_score", 101),
    ("max_allowed_slippage", -0.1), ("max_allowed_deviation", -0.1),
])
def test_blocks_invalid_limits(field, value):
    assert run_gate(**{field: value})["status"] == "BLOCK"


@pytest.mark.parametrize("field", [
    "slippage", "deviation", "output", "minimum",
    "max_allowed_score", "max_allowed_slippage", "max_allowed_deviation",
])
@pytest.mark.parametrize("bad_value", [float("nan"), float("inf"), float("-inf")])
def test_blocks_non_finite_numeric_inputs(field, bad_value):
    assert run_gate(**{field: bad_value})["status"] == "BLOCK"


@pytest.mark.parametrize("field", [
    "slippage", "deviation", "output", "minimum",
    "max_allowed_score", "max_allowed_slippage", "max_allowed_deviation",
])
def test_blocks_missing_numeric_inputs(field):
    assert run_gate(**{field: None})["status"] == "BLOCK"


@pytest.mark.parametrize("assessment", [
    None, {}, {"status": "insufficient_data", "score": None},
    {"status": "assessed", "score": float("nan")},
    {"status": "assessed", "score": float("inf")},
    {"status": "assessed", "score": -1},
    {"status": "assessed", "score": 101},
    {"status": "unknown", "score": 0},
])
def test_blocks_invalid_assessment(assessment):
    assert run_gate(assessment=assessment)["status"] == "BLOCK"


def test_blocks_slippage_over_limit():
    assert run_gate(slippage=0.6)["status"] == "BLOCK"


def test_blocks_deviation_over_absolute_limit():
    assert run_gate(deviation=-1.1)["status"] == "BLOCK"


def test_blocks_score_over_limit():
    assert run_gate(assessment=good_assessment(51))["status"] == "BLOCK"


@pytest.mark.parametrize("output,minimum", [(0, 0), (-1, 1), (100, 101)])
def test_blocks_invalid_or_inconsistent_output(output, minimum):
    assert run_gate(output=output, minimum=minimum)["status"] == "BLOCK"


def test_assess_marks_invalid_inputs_insufficient():
    result = assess(float("nan"), 0.1, 0.2)
    assert result["status"] == "insufficient_data"
    assert result["score"] is None


def test_assess_valid_inputs_returns_bounded_score():
    result = assess(0.1, 0.2, 0.3)
    assert result["status"] == "assessed"
    assert 0 <= result["score"] <= 100


def test_equal_limits_are_allowed():
    result = run_gate(slippage=0.5, deviation=1.0, assessment=good_assessment(50))
    assert result["status"] == "PASS (analysis gate only)"


def test_gate_never_claims_execution_or_chain_blocking():
    result = run_gate()
    assert result["execution_performed"] is False
    assert result["does_not_block_onchain_transactions"] is True
