from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np


SUBPROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SUBPROJECT))

from joint_premium import (  # noqa: E402
    combine_premiums_bps,
    factor_dependence,
    validate_correlation_matrix,
    weighted_correlation,
)


class JointMathTests(unittest.TestCase):
    def test_component_reduction_identities(self) -> None:
        self.assertEqual(combine_premiums_bps(10, 0, None)["central_bps"], 10)
        self.assertEqual(combine_premiums_bps(0, 4, None)["central_bps"], 4)

    def test_correlation_boundaries(self) -> None:
        self.assertEqual(combine_premiums_bps(10, 4, 1)["central_bps"], 14)
        self.assertEqual(combine_premiums_bps(10, 4, -1)["central_bps"], 6)
        self.assertAlmostEqual(
            combine_premiums_bps(10, 4, 0)["central_bps"], np.hypot(10, 4)
        )

    def test_weighted_correlation(self) -> None:
        corr = weighted_correlation(
            np.array([1.0, 2.0, 3.0]),
            np.array([2.0, 4.0, 6.0]),
            np.array([0.2, 0.3, 0.5]),
        )
        self.assertAlmostEqual(corr, 1.0)

    def test_factor_dependence_matches_single_factor(self) -> None:
        result = factor_dependence(np.array([2.0, 0.0]), np.eye(2), 0.8)
        self.assertAlmostEqual(result["rho_transition_carbon"], 1.0)
        self.assertAlmostEqual(result["rho_transition_gap"], 0.8)

    def test_non_psd_matrix_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            validate_correlation_matrix(
                np.array([[1.0, 0.9, 0.9], [0.9, 1.0, -0.9], [0.9, -0.9, 1.0]])
            )


if __name__ == "__main__":
    unittest.main()

