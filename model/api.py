"""CAP 계산기 API — 파일을 건드리지 않는 순수 계산 진입점.

CAP은 계산기다: 시나리오·파라미터 오버라이드 in → anatomy·수준 out.
웹은 outputs/를 읽고, 이 모듈은 나중에 MCP 서버가 감쌀 시임(seam)이다.

    from model.api import compute
    compute({"pricing": {"lambda": 0.6},
             "sigmas": {"carbon_diffusion": 0.5},
             "carbon_scenarios": [
                 {"scenario": "SQ", "level_usd": 12, "prob": 0.5, "binds": 0},
                 {"scenario": "REFORM", "level_usd": 60, "prob": 0.5, "binds": 1}]})

오버라이드는 메모리에서만 적용된다 — config 파일·outputs/ 불변.
LSM(τ*)은 재계산하지 않고 outputs/tau_star.json의 전환연도를 쓴다
(τ* 재계산 포함 풀 런은 make model).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from model.lib.anatomy import DRIVERS, euler_shares  # noqa: E402
from model.lib.finance import annuity  # noqa: E402
from model.lib.jump import binding_level, scenario_mean_level, sigma_carbon_combined  # noqa: E402
from model.s02_calibrate import load_calibration  # noqa: E402
from model.s04_anatomy import BPS, anatomy_for, firm_exposures, firm_frame  # noqa: E402


def compute(overrides: dict | None = None) -> dict:
    """오버라이드 적용 계산. 반환: {firms: [{shares, premium_bps, ...}], derived: {...}}."""
    ov = overrides or {}
    cal = load_calibration()

    for driver, val in ov.get("sigmas", {}).items():
        i = cal.sigmas.index[cal.sigmas["driver"] == driver][0]
        cal.sigmas.loc[i, "value"] = float(val)
    for param, val in ov.get("pricing", {}).items():
        cal.pricing[param] = float(val)
    if "carbon_scenarios" in ov:
        scen = pd.DataFrame(ov["carbon_scenarios"])
        levels = scen["level_usd"].to_numpy(float)
        probs = scen["prob"].to_numpy(float)
        binds = scen["binds"].to_numpy(int)
        if abs(probs.sum() - 1.0) > 1e-9:
            raise ValueError("carbon_scenarios prob 합 ≠ 1")
        cal.l_bar = scenario_mean_level(levels, probs)
        cal.l_bind = binding_level(levels, probs, binds)
        cal.sigma_carbon_reform = sigma_carbon_combined(
            cal.sigma("carbon_diffusion"), levels, probs
        )

    frame = firm_frame(cal)
    priced = frame[frame["category"] == "priced_route"]
    firms = []
    for fid, g in priced.groupby("firm_id", sort=True):
        meta = firm_exposures(cal, g)
        base = anatomy_for(cal, meta, cal.sigma("carbon_diffusion"))
        reform = anatomy_for(cal, meta, cal.sigma_carbon_reform)
        firms.append(
            {
                "firm_id": fid,
                "firm": meta["firm"],
                "route": meta["route"],
                "shares": base["shares"],
                "shares_reform": reform["shares"],
                "premium_bps": base["premium_bps"],
                "premium_reform_bps": reform["premium_bps"],
                "sigma_b_usd_bn": base["sigma_b_usd_bn"],
            }
        )
    return {
        "firms": firms,
        "derived": {
            "l_bar": cal.l_bar,
            "l_bind": cal.l_bind,
            "sigma_carbon_reform": cal.sigma_carbon_reform,
        },
        "note": "τ*는 outputs/tau_star.json 고정 — LSM 재계산은 make model",
    }


if __name__ == "__main__":
    import json

    print(json.dumps(compute(), ensure_ascii=False, indent=2))
