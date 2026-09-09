#!/usr/bin/env bash
# Wrapper to run the `ur5e-record` console script with a PYTHONPATH that
# prefers the actual package subfolders inside the keyteleop repo. This avoids
# the outer-folder name-shadowing that can make imports resolve to the wrong
# location when running from the repo root.
# Usage: ./scripts/run_ur5e_record.sh [args]

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

PYTHONPATH="$PROJECT_ROOT/third_party/lerobot/src:$PROJECT_ROOT/third_party/lerobot_ur5e_keyteleop/scripts:$PROJECT_ROOT/third_party/lerobot_ur5e_keyteleop/lerobot_robot_ur5e:$PROJECT_ROOT/third_party/lerobot_ur5e_keyteleop/lerobot_teleoperator_ur5e"
export PYTHONPATH

exec "$PROJECT_ROOT/venv/bin/ur5e-record" "$@"
