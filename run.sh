#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 tests/test_policy.py
python3 tests/test_policy.py --benchmark
python3 run.py --seed 1000 --render
