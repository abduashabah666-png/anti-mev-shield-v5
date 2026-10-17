from gate_logic import assess, evaluate_gate


def normal_assessment():
    return assess(deviation=0.2, slippage=0.5, sensitivity=0.1)


def run_gate(**overrides):
    values = {
        "assessment": normal_assessment(),
        "slippage": 0.5,
        "deviation": 0.2,
        "output": 240.0,
        "minimum": 239.0,
        "max_allowed_score": 24,
        "max_allowed_slippage": 0.5,
        "max_allowed_deviation": 1.0,
    }
    values.update(overrides)
    return evaluate_gate(**values)


def test_pass_when_all_values_are_within_limits():
    result = run_gate()
    assert result["status"] == "PASS (analysis gate only)"
    assert result["reasons"] == []


def test_block_when_slippage_exceeds_limit():
    result = run_gate(max_allowed_slippage=0.1)
    assert result["status"] == "BLOCK"
    assert any("Slippage" in reason for reason in result["reasons"])


def test_block_when_deviation_exceeds_limit():
    result = run_gate(deviation=2.0)
    assert result["status"] == "BLOCK"
    assert any("reference deviation" in reason for reason in result["reasons"])


def test_block_when_score_exceeds_limit():
    assessment = assess(deviation=5.0, slippage=0.5, sensitivity=0.1)
    result = run_gate(assessment=assessment, deviation=5.0, max_allowed_deviation=10.0)
    assert result["status"] == "BLOCK"
    assert any("Heuristic score" in reason for reason in result["reasons"])


def test_block_when_analysis_data_is_missing():
    assessment = assess(deviation=None, slippage=0.5, sensitivity=0.1)
    result = run_gate(assessment=assessment, deviation=None)
    assert result["status"] == "BLOCK"
    assert any("analysis data is missing" in reason for reason in result["reasons"])


def test_block_when_output_is_zero():
    result = run_gate(output=0.0)
    assert result["status"] == "BLOCK"
    assert any("not positive" in reason for reason in result["reasons"])


def test_block_when_minimum_output_is_negative():
    result = run_gate(minimum=-1.0)
    assert result["status"] == "BLOCK"
    assert any("not positive" in reason for reason in result["reasons"])


def test_equal_slippage_limit_is_allowed():
    result = run_gate(slippage=0.5, max_allowed_slippage=0.5)
    assert result["status"] == "PASS (analysis gate only)"


def test_equal_deviation_limit_is_allowed():
    assessment = assess(deviation=1.0, slippage=0.5, sensitivity=0.1)
    result = run_gate(assessment=assessment, deviation=1.0, max_allowed_deviation=1.0)
    assert result["status"] == "PASS (analysis gate only)"


def test_gate_does_not_execute_transactions():
    result = run_gate()
    assert result["execution_performed"] is False
    assert result["does_not_block_onchain_transactions"] is True


def test_block_when_minimum_exceeds_output():
    result = run_gate(output=240.0, minimum=250.0)
    assert result["status"] == "BLOCK"
    assert any("Minimum output exceeds estimated output" in reason for reason in result["reasons"])


def test_block_when_output_is_not_finite():
    result = run_gate(output=float("inf"))
    assert result["status"] == "BLOCK"
    assert any("finite numbers" in reason for reason in result["reasons"])
