# CAP — make all = ingest → calibration → model → anchors → ledger → theory → test → web
PY := uv run python

.PHONY: all ingest calibration model check-anchors ledger render-theory test web clean

all: ingest calibration model check-anchors ledger render-theory test web

ingest:
	$(PY) model/s01_ingest.py

calibration:
	$(PY) scripts/build_calibration.py

model: calibration
	$(PY) model/run_all.py

check-anchors:
	$(PY) scripts/check_anchors.py

ledger:
	$(PY) scripts/gen_ledger.py
	$(PY) scripts/gen_refs_index.py

render-theory:
	$(PY) scripts/render_theory.py

test: calibration
	uv run pytest model/tests/ -q

web: render-theory
	cd web && npm run build

clean:
	rm -rf data/processed/*.parquet outputs/*.json web/out web/.next web/content/theory
