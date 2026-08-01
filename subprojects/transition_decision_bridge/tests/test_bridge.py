from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SUBPROJECT = HERE.parent
REPO_ROOT = SUBPROJECT.parents[1]
sys.path.insert(0, str(SUBPROJECT))

from bridge import AGGREGATION_STATUS, build_artifact, render_markdown  # noqa: E402


class BridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.underwriting = json.loads(
            (REPO_ROOT / "outputs" / "transition_underwriting.json").read_text()
        )
        cls.gap_loss = json.loads(
            (REPO_ROOT / "outputs" / "alignment_gap_loss.json").read_text()
        )
        cls.artifact = build_artifact(cls.underwriting, cls.gap_loss)

    def test_all_underwritten_firms_are_included(self) -> None:
        expected = {row["firm_id"] for row in self.underwriting["firms"]}
        actual = {row["firm_id"] for row in self.artifact["firms"]}
        self.assertEqual(actual, expected)

    def test_headline_and_overlay_match_sources(self) -> None:
        source_uw = {row["firm_id"]: row for row in self.underwriting["firms"]}
        source_gap = {row["firm_id"]: row for row in self.gap_loss["firms"]}
        for row in self.artifact["firms"]:
            firm_id = row["firm_id"]
            self.assertAlmostEqual(
                row["decision_ready_risk_premium"]["headline_bps"],
                source_uw[firm_id]["underwriting"]["model_implied_spread_bps"],
            )
            self.assertAlmostEqual(
                row["alignment_gap_overlay"]["overlay_bps"],
                source_gap[firm_id]["gap_risk_charge_bps"],
            )

    def test_separate_bases_are_never_summed(self) -> None:
        self.assertIsNone(self.artifact["portfolio"]["combined_total_bps"])
        self.assertEqual(
            self.artifact["portfolio"]["aggregation_status"], AGGREGATION_STATUS
        )
        for row in self.artifact["firms"]:
            publication = row["final_premium_publication"]
            self.assertIsNone(publication["combined_total_bps"])
            self.assertEqual(publication["aggregation_status"], AGGREGATION_STATUS)

    def test_alignment_safe_recommendation_never_increases_gap(self) -> None:
        for row in self.artifact["firms"]:
            option = row["decision_options"]["best_alignment_safe_de_risker"]
            if option is not None:
                self.assertGreater(option["headline_reduction_bps"], 0)
                self.assertLessEqual(option["alignment_gap_change_mtco2"], 0)

    def test_no_tradeoff_recommendation_never_increases_either_basis(self) -> None:
        for row in self.artifact["firms"]:
            option = row["decision_options"]["best_no_tradeoff_de_risker"]
            if option is not None:
                self.assertGreater(option["headline_reduction_bps"], 0)
                self.assertLessEqual(option["alignment_gap_change_mtco2"], 0)
                self.assertLessEqual(option["gap_overlay_change_bps"], 0)

    def test_markdown_states_publication_control(self) -> None:
        report = render_markdown(self.artifact)
        self.assertIn("not published — separate bases", report)
        self.assertIn("conditional enterprise transition risk premium", report)


if __name__ == "__main__":
    unittest.main()
