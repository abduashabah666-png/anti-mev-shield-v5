import unittest
from decimal import Decimal
from app import assess, evaluate_gate


class GateTests(unittest.TestCase):
    def setUp(self):
        self.ok_assessment = assess(0.2, 0.5, 0.2)

    def test_pass_when_all_checks_are_within_limits(self):
        result = evaluate_gate(self.ok_assessment, 0.5, 0.2, Decimal("10"), Decimal("9.95"))
        self.assertEqual(result["status"], "PASS (analysis gate only)")
        self.assertEqual(result["reasons"], [])

    def test_block_when_score_exceeds_limit(self):
        result = evaluate_gate(assess(3, 0.5, 0.2), 0.5, 3, Decimal("10"), Decimal("9.95"))
        self.assertEqual(result["status"], "BLOCK")
        self.assertTrue(any("Heuristic score" in reason for reason in result["reasons"]))

    def test_block_when_slippage_exceeds_limit(self):
        result = evaluate_gate(self.ok_assessment, 0.6, 0.2, Decimal("10"), Decimal("9.9"))
        self.assertEqual(result["status"], "BLOCK")
        self.assertTrue(any("Slippage" in reason for reason in result["reasons"]))

    def test_block_when_absolute_deviation_exceeds_limit(self):
        result = evaluate_gate(self.ok_assessment, 0.5, -1.2, Decimal("10"), Decimal("9.95"))
        self.assertEqual(result["status"], "BLOCK")
        self.assertTrue(any("Absolute reference deviation" in reason for reason in result["reasons"]))

    def test_block_when_required_analysis_data_is_missing(self):
        result = evaluate_gate(assess(None, 0.5, None), 0.5, None, Decimal("10"), Decimal("9.95"))
        self.assertEqual(result["status"], "BLOCK")
        self.assertTrue(any("Required analysis data is missing" in reason for reason in result["reasons"]))

    def test_block_when_output_is_not_positive(self):
        result = evaluate_gate(self.ok_assessment, 0.5, 0.2, Decimal("0"), Decimal("9.95"))
        self.assertEqual(result["status"], "BLOCK")

    def test_block_when_minimum_is_not_positive(self):
        result = evaluate_gate(self.ok_assessment, 0.5, 0.2, Decimal("10"), Decimal("-1"))
        self.assertEqual(result["status"], "BLOCK")

    def test_equal_limits_are_allowed(self):
        result = evaluate_gate(
            assess(0.2, 0.5, 0.2), 0.5, 1.0, Decimal("10"), Decimal("9.95"),
            max_allowed_score=24, max_allowed_slippage=0.5, max_allowed_deviation=1.0
        )
        self.assertEqual(result["status"], "PASS (analysis gate only)")

    def test_missing_deviation_blocks(self):
        result = evaluate_gate(self.ok_assessment, 0.5, None, Decimal("10"), Decimal("9.95"))
        self.assertEqual(result["status"], "BLOCK")


if __name__ == "__main__":
    unittest.main(verbosity=2)
