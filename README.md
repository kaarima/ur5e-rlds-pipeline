# UR5e RTDE Smoke Test

This project verifies that Python can read state from URSim over RTDE before
building the demonstration-recording pipeline.

## Prerequisites

Launch URSim with `-p 30004:30004` in addition to its existing VNC and web
port mappings.

On Ubuntu, install the `venv` support package once if it is not already
available:

```bash
sudo apt-get update
sudo apt-get install -y python3.10-venv
```

## Setup and run

From this directory, create and activate the virtual environment, install the
only Python dependency, and run the test:

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
python src/rtde_test.py
```

If the first command reports that `ensurepip` is unavailable and you cannot
install the Ubuntu package, create a standard venv without its bundled pip and
bootstrap pip into that venv from the system installation:

```bash
python3 -m venv --clear --without-pip venv
python3 -m pip install --target venv/lib/python3.10/site-packages pip
source venv/bin/activate
python -m pip install -r requirements.txt
python src/rtde_test.py
```

On success, the script prints the six joint positions in radians and the TCP
pose as `[x, y, z, rx, ry, rz]` in metres and radians. When finished, leave the
environment with:

```bash
deactivate
```

## Running the recorder (keyteleop)

The `ur5e-record` console script included with the keyteleop integration must be
run with a PYTHONPATH that prefers the actual package subfolders inside the
repository. The keyteleop repo contains both an outer folder and an inner
Python package folder that share similar names (for example,
`lerobot_robot_ur5e/` and `lerobot_robot_ur5e/lerobot_robot_ur5e/`). If you add
the repo root to `PYTHONPATH` (or run from the repo root) Python's import
resolution can become ambiguous and cause imports to resolve to the outer
folder rather than the package `__init__.py`, producing errors like
`ImportError: cannot import name 'UR5eConfig' from 'lerobot_robot_ur5e' (unknown location)`.

To avoid this, use the provided wrapper which sets `PYTHONPATH` to the
inner-package folders and the `scripts` folder before calling the installed
console script:

```bash
./scripts/run_ur5e_record.sh
```

This runs the same `ur5e-record` entrypoint but ensures imports resolve to the
correct package files. If you prefer, you can replicate the same `PYTHONPATH`
value manually; the wrapper is a convenience to make the command reproducible.

Note (known-issue): a thin runner package that exposes a clean console-script
entrypoint without requiring a manual PYTHONPATH would be a more robust long-
term fix. This is logged as a TODO in the repository for future work.

## Dependencies

This repository does NOT vendor `third_party/lerobot_ur5e_keyteleop` because
its upstream source does not have a clearly redistributable license.
Install that dependency separately before running the recorder. From the
project root, run:

```bash
git clone https://github.com/scy-v/lerobot_ur5e_keyteleop.git third_party/lerobot_ur5e_keyteleop
pip install -r third_party/lerobot_ur5e_keyteleop/requirements.txt
```

If you prefer editable installs (recommended for development):

```bash
pip install -e third_party/lerobot_ur5e_keyteleop/lerobot_robot_ur5e --no-deps
pip install -e third_party/lerobot_ur5e_keyteleop/lerobot_teleoperator_ur5e --no-deps
```


