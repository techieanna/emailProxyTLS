#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}/.."

PATCH_DIR="peoplesoft_patch_orchestrator/examples/patches/Jan2026"

echo "[1/4] Syntax compile"
python -m py_compile $(rg --files peoplesoft_patch_orchestrator -g '*.py')

echo "[2/4] Unit and smoke tests"
python -m unittest discover -s peoplesoft_patch_orchestrator/tests -p 'test_*.py' -v

echo "[3/4] End-to-end dry-run simulation"
python -m peoplesoft_patch_orchestrator.orchestrator \
  --patch-dir="${PATCH_DIR}" \
  --auto \
  --dry-run \
  --simulation-mode \
  --compliance-mode

echo "[4/4] Artifact validation"
shopt -s nullglob
reports=(peoplesoft_patch_orchestrator/logs/reports/*.json)
metrics=(peoplesoft_patch_orchestrator/logs/metrics_*.prom)
graphs=(peoplesoft_patch_orchestrator/logs/graph_*.json)

[[ -f peoplesoft_patch_orchestrator/logs/state.db ]] || { echo "state.db missing"; exit 1; }
[[ ${#reports[@]} -gt 0 ]] || { echo "report json missing"; exit 1; }
[[ ${#metrics[@]} -gt 0 ]] || { echo "metrics file missing"; exit 1; }
[[ ${#graphs[@]} -gt 0 ]] || { echo "graph file missing"; exit 1; }

echo "SUCCESS: self-test passed"
