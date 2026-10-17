import unittest
from app import assess

class AssessTests(unittest.TestCase):
    def test_low_indicators(self):
        result = assess(0.4, 0.1, 0.01)
        self.assertEqual(result["score_out_of_100"], 0)
        self.assertEqual(result["status"], "indicators_available")
        self.assertEqual(result["label"], "Lower indicator level")

    def test_high_slippage(self):
        result = assess(0.4, 5.0, 0.01)
        self.assertEqual(result["score_out_of_100"], 25)
        self.assertEqual(result["label"], "Moderate indicator level")

    def test_large_deviation_and_sensitivity(self):
        result = assess(-6.0, 1.2, 6.0)
        self.assertEqual(result["score_out_of_100"], 82)
        self.assertEqual(result["label"], "High indicator level")

    def test_missing_reference_is_not_low(self):
        result = assess(None, 0.1, 0.01)
        self.assertEqual(result["status"], "insufficient_data")
        self.assertEqual(result["label"], "Insufficient data")
        self.assertIn("External reference deviation is unavailable.", result["missing_data"])

    def test_missing_sensitivity_is_not_low(self):
        result = assess(0.2, 0.1, None)
        self.assertEqual(result["status"], "insufficient_data")
        self.assertEqual(result["label"], "Insufficient data")

if __name__ == "__main__":
    unittest.main()
