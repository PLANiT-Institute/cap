"""make model 진입점: s02→s11 + outputs/manifest.json (lineage 포함).

manifest: 실행 시각, config/코드/raw/processed/lock 해시, git SHA+dirty,
seed, T_required 출처, artifact 목록. dirty tree는 숨기지 않는다.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from model import (  # noqa: E402
    s02_calibrate,
    s03_lsm,
    s04_anatomy,
    s05_robustness,
    s06_interventions,
    s07_pathways,
    s08_underwriting,
    s09_deal_screening,
    s10_result_contract,
    s11_pilot_cases,
    s12_level_wedge,
)


# 생성물 — 편집 정본은 config/sheets/*.csv다. xlsx는 make calibration이 매번 새로
# 조립하며 zip 메타데이터가 바뀌어, 셀 값이 동일해도 바이트 해시가 달라진다.
# lineage에 그 노이즈를 넣지 않기 위해 해시 대상에서 제외한다.
GENERATED_ARTIFACTS = {"calibration.xlsx"}


def tree_hash(paths: list[Path], patterns: tuple[str, ...] = ("*",)) -> str:
    h = hashlib.sha256()
    for base in paths:
        if not base.exists():
            continue
        for pat in patterns:
            for p in sorted(base.rglob(pat)):
                if (p.is_file() and "__pycache__" not in p.parts
                        and p.name != ".DS_Store"
                        and p.name not in GENERATED_ARTIFACTS):
                    h.update(p.relative_to(ROOT).as_posix().encode())
                    h.update(p.read_bytes())
    return h.hexdigest()


def git_info() -> tuple[str, bool]:
    try:
        sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                             capture_output=True, text=True).stdout.strip() or "unknown"
        dirty = bool(subprocess.run(["git", "status", "--porcelain"], cwd=ROOT,
                                    capture_output=True, text=True).stdout.strip())
        return sha, dirty
    except OSError:
        return "unknown", True


def main() -> int:
    for stage in (s02_calibrate, s03_lsm, s04_anatomy, s05_robustness,
                  s06_interventions, s07_pathways, s08_underwriting,
                  s09_deal_screening, s10_result_contract, s11_pilot_cases,
                  s12_level_wedge):
        rc = stage.main()
        if rc:
            return rc
    cal = s02_calibrate.load_calibration()
    sha, dirty = git_info()
    manifest = {
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_sha": sha,
        "git_dirty": dirty,
        "code_sha256": tree_hash([ROOT / "model", ROOT / "scripts"], ("*.py",)),
        "config_sha256": tree_hash([ROOT / "config"]),
        "raw_data_sha256": tree_hash([ROOT / "data" / "raw"]),
        "processed_data_sha256": tree_hash([ROOT / "data" / "processed"]),
        "dependency_lock_sha256": hashlib.sha256((ROOT / "uv.lock").read_bytes()).hexdigest()
        if (ROOT / "uv.lock").exists() else None,
        "seed": int(cal.lsm["seed"]),
        "t_required_source": cal.t_required_source,
        "measured_overrides": cal.measured_overrides,
        "artifacts": sorted(p.name for p in (ROOT / "outputs").glob("*.json")
                            if p.name != "manifest.json"),
        "pilot_reports": sorted(
            p.relative_to(ROOT).as_posix()
            for p in (ROOT / "outputs" / "pilots").glob("*.md")
        ),
    }
    (ROOT / "outputs" / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    )
    print(
        f"OK — manifest (config {manifest['config_sha256'][:12]}…, "
        f"dirty={dirty}, T_required={manifest['t_required_source']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
