.PHONY: all run run-joint test

all: run run-joint test

run:
	python3 run.py

run-joint:
	cd ../.. && uv run python subprojects/transition_decision_bridge/run_joint.py

test:
	cd ../.. && uv run python -m unittest discover -s subprojects/transition_decision_bridge/tests -v
