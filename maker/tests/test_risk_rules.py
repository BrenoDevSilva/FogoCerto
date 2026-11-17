import unittest
from simulation.mock_data import SCENARIOS, classify_local, consolidate_risk

class RiskRuleTests(unittest.TestCase):
    def test_gold_level_is_never_downgraded(self):
        self.assertEqual(consolidate_risk("ALTO", "BAIXO"), "ALTO")
        self.assertEqual(consolidate_risk("MEDIO", "BAIXO"), "MEDIO")

    def test_local_level_can_escalate_gold(self):
        self.assertEqual(consolidate_risk("BAIXO", "ALTO"), "ALTO")

    def test_unknown_gold_uses_local(self):
        self.assertEqual(consolidate_risk("INDEFINIDO", "MEDIO"), "MEDIO")

    def test_expected_scenario_classification(self):
        self.assertEqual([classify_local(x) for x in SCENARIOS],
                         ["BAIXO", "MEDIO", "ALTO"])

if __name__ == "__main__":
    unittest.main()
