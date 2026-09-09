#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WRAPPER="$PROJECT_ROOT/scripts/run_ur5e_record.sh"
WORKFLOW="$PROJECT_ROOT/.github/workflows/smoke-test.yml"

if [ ! -f "$WRAPPER" ]; then
  echo "[FAIL] Wrapper script not found: $WRAPPER"
  exit 2
fi

if [ ! -x "$WRAPPER" ]; then
  echo "[FAIL] Wrapper script is not executable: $WRAPPER"
  exit 3
fi

PYTHONPATH_LINE="$(grep -m1 '^PYTHONPATH=' "$WRAPPER" || true)"
if [ -z "$PYTHONPATH_LINE" ]; then
  echo "[FAIL] Could not find PYTHONPATH assignment in wrapper: $WRAPPER"
  exit 4
fi

PYTHONPATH_VALUE="${PYTHONPATH_LINE#PYTHONPATH=\"}"
PYTHONPATH_VALUE="${PYTHONPATH_VALUE%\"}"
PYTHONPATH_VALUE="${PYTHONPATH_VALUE//\$PROJECT_ROOT/$PROJECT_ROOT}"

echo "[OK] Wrapper exists and is executable: $WRAPPER"
echo "[INFO] Verifying wrapper PYTHONPATH entries exist on disk..."

IFS=':' read -r -a PYTHONPATH_ENTRIES <<< "$PYTHONPATH_VALUE"
for entry in "${PYTHONPATH_ENTRIES[@]}"; do
  if [[ "$entry" != "$PROJECT_ROOT/"* ]]; then
    echo "[FAIL] PYTHONPATH entry is not rooted in the repository: $entry"
    exit 5
  fi

  if [ ! -e "$entry" ]; then
    echo "[FAIL] PYTHONPATH entry does not exist: $entry"
    exit 6
  fi

  echo "[OK] PYTHONPATH entry exists: $entry"
done

echo "[INFO] Checking that the workflow documents the clone targets..."
if ! grep -Fq 'git clone --depth 1 --branch v0.4.0 --single-branch https://github.com/huggingface/lerobot.git third_party/lerobot' "$WORKFLOW"; then
  echo "[FAIL] Workflow does not document the LeRobot clone target"
  exit 7
fi

if ! grep -Fq 'git clone --depth 1 https://github.com/scy-v/lerobot_ur5e_keyteleop.git third_party/lerobot_ur5e_keyteleop' "$WORKFLOW"; then
  echo "[FAIL] Workflow does not document the keyteleop clone target"
  exit 8
fi

echo "[OK] Workflow documents the required clone targets"

echo "[INFO] Parsing key Python files for syntax only..."

python3 - "$PROJECT_ROOT" <<'PY'
from __future__ import annotations

import ast
import sys
from pathlib import Path

project_root = Path(sys.argv[1])
python_files = [
    project_root / "src/rtde_test.py",
    project_root / "third_party/lerobot_ur5e_keyteleop/lerobot_robot_ur5e/lerobot_robot_ur5e/config_ur5e.py",
    project_root / "third_party/lerobot_ur5e_keyteleop/lerobot_robot_ur5e/lerobot_robot_ur5e/dummy_camera.py",
    project_root / "third_party/lerobot_ur5e_keyteleop/lerobot_robot_ur5e/lerobot_robot_ur5e/ur5e.py",
]

for path in python_files:
    ast.parse(path.read_text(), filename=str(path))
    print(f"[OK] AST syntax valid: {path}")
PY

echo "[PASS] Static smoke test completed successfully."
