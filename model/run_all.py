"""make model 진입점: s02→s06 실행 + outputs/manifest.json.

manifest: 실행 시각, config 해시(전 config 파일 SHA256), git SHA, seed, t_gcam_source.
config만 바꾸면 코드 수정 없이 전체 결과가 재생성되고 해시가 바뀐다 (Phase 2 완료 기준).
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

from model import s02_calibrate, s03_lsm, s04_anatomy, s05_robustness, s06_contracts  # noqa: E402


def config_hash() -> str:
    h = hashlib.sha256()
    for p in sorted((ROOT / "config").rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts:
            h.update(p.relative_to(ROOT).as_posix().encode())
            h.update(p.read_bytes())
    return h.hexdigest()


def git_sha() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True
        ).stdout.strip() or "unknown"
    except OSError:
        return "unknown"


def main() -> int:
    for stage in (s02_calibrate, s03_lsm, s04_anatomy, s05_robustness, s06_contracts):
        rc = stage.main()
        if rc:
            return rc
    cal = s02_calibrate.load_calibration()
    manifest = {
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "config_sha256": config_hash(),
        "git_sha": git_sha(),
        "seed": int(cal.lsm["seed"]),
        "t_gcam_source": cal.t_gcam_source,
        "measured_overrides": cal.measured_overrides,
        "artifacts": sorted(p.name for p in (ROOT / "outputs").glob("*.json") if p.name != "manifest.json"),
    }
    (ROOT / "outputs" / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    )
    print(f"OK — manifest (config {manifest['config_sha256'][:12]}…, t_gcam={manifest['t_gcam_source']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
