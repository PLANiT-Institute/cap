from __future__ import annotations

import sys
import unittest
from pathlib import Path


SUBPROJECT = Path(__file__).resolve().parent.parent
REPO_ROOT = SUBPROJECT.parents[1]
sys.path.insert(0, str(SUBPROJECT))

from joint_inputs import RECONCILIATION_TOLERANCE, build_joint_artifact  # noqa: E402


class JointReconciliationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.artifact = build_joint_artifact(REPO_ROOT)

    def test_all_six_underwritten_firms_are_present(self) -> None:
        self.assertEqual(self.artifact["portfolio"]["firm_count"], 6)

    def test_components_reconcile(self) -> None:
        for firm in self.artifact["firms"]:
            rec = firm["base"]["reconciliation"]
            self.assertLessEqual(
                rec["sigma_abs_error_usd_bn"], RECONCILIATION_TOLERANCE
            )
            self.assertLessEqual(rec["premium_abs_error_bps"], RECONCILIATION_TOLERANCE)

    def test_combined_premium_respects_bounds(self) -> None:
        for firm in self.artifact["firms"]:
            combined = firm["base"]["combined"]
            self.assertGreaterEqual(
                combined["central_bps"], combined["mathematical_lower_bps"]
            )
            self.assertLessEqual(
                combined["central_bps"], combined["perfect_positive_upper_bps"]
            )

    def test_probability_is_not_multiplied_in_covariance(self) -> None:
        control = self.artifact["method"]["probability_control"]
        self.assertIn("p_bind remains embedded once", control)
        for firm in self.artifact["firms"]:
            lineage = firm["base"]["factor_lineage"]["probability_treatment"]
            self.assertIn("correlation changes covariance only", lineage)

    def test_no_tradeoff_recommendation_respects_all_components(self) -> None:
        for firm in self.artifact["firms"]:
            option = firm["decision"]["best_no_tradeoff_de_risker"]
            if option is not None:
                self.assertGreater(option["combined_reduction_bps"], 0)
                self.assertLessEqual(option["alignment_gap_change_mtco2"], 0)
                self.assertLessEqual(option["gap_overlay_change_bps"], 0)

    def test_evidence_and_promotion_gates_remain_closed(self) -> None:
        self.assertEqual(
            self.artifact["publication_gate"]["status"], "SUBPROJECT_PROVISIONAL"
        )
        self.assertFalse(self.artifact["publication_gate"]["core_or_web_promoted"])
        self.assertTrue(
            all(firm["evidence_grade"] == "PROVISIONAL" for firm in self.artifact["firms"])
        )


if __name__ == "__main__":
    unittest.main()

