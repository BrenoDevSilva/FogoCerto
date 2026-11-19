import unittest
from simulation.mock_data import SCENARIOS, classify_local

class MockDataTests(unittest.TestCase):
    def test_all_scenario_levels(self):
        self.assertEqual([classify_local(x) for x in SCENARIOS],
                         ["BAIXO", "MEDIO", "ALTO"])

    def test_smoke_escalates_to_high(self):
        sample = {"temperatureC": 20, "humidityPct": 70, "smokeDetected": True}
        self.assertEqual(classify_local(sample), "ALTO")

if __name__ == "__main__":
    unittest.main()
