#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WRAPPER="$PROJECT_ROOT/scripts/run_ur5e_record.sh"

if [ ! -f "$WRAPPER" ]; then
  echo "[FAIL] Wrapper script not found: $WRAPPER"
  exit 2
fi

if [ ! -x "$WRAPPER" ]; then
  echo "[FAIL] Wrapper script is not executable: $WRAPPER"
  exit 3
fi

# Reconstruct the PYTHONPATH the wrapper sets and test import using the venv python
PYTHONPATH="$PROJECT_ROOT/third_party/lerobot_ur5e_keyteleop/scripts:$PROJECT_ROOT/third_party/lerobot_ur5e_keyteleop/lerobot_robot_ur5e/lerobot_robot_ur5e:$PROJECT_ROOT/third_party/lerobot_ur5e_keyteleop/lerobot_teleoperator_ur5e/lerobot_teleoperator_ur5e"

echo "[OK] Wrapper exists and is executable: $WRAPPER"
echo "[INFO] Testing import of lerobot_robot_ur5e using venv python..."

env PYTHONPATH="$PYTHONPATH" "$PROJECT_ROOT/venv/bin/python" -c "import lerobot_robot_ur5e; print('IMPORT_OK', lerobot_robot_ur5e.__file__)"

echo "[PASS] Smoke test completed successfully."
