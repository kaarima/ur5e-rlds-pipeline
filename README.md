# UR5e RLDS Pipeline

Collects teleoperated demonstrations from a simulated UR5e robot (URSim) and converts
them into RLDS format for training imitation-learning / VLA models.

```
Simulated UR5e (URSim) → Keyboard Teleoperation (LeRobot) → Recorded Episodes
→ RLDS Dataset
```

## Status

Core pipeline complete and validated end-to-end: simulated robot control, keyboard
teleoperation with synchronized recording, dual synthetic camera views (rendered live
from the robot's true pose via PyBullet), and a working LeRobot → RLDS conversion
script with full validation.

See `RLDS_Target_Schema.pdf` for the full data schema.

## Prerequisites

- Docker
- Python 3.10, `venv`
- ROS Humble (`ros-humble-ur-description`, `ros-humble-xacro`) — used to generate the
  UR5e 3D model for the synthetic camera renderer

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Launch URSim with all required ports (RTDE, Dashboard, and control ports — not just
VNC/web):
```bash
docker run --rm -it \
  -p 5900:5900 -p 6080:6080 -p 29999:29999 \
  -p 30001-30003:30001-30003 -p 30004:30004 -p 30020:30020 \
  -p 50001-50003:50001-50003 \
  --name ursim universalrobots/ursim_e-series
```

In PolyScope (`http://localhost:6080/vnc.html?host=localhost&port=6080`): power on the
robot and switch **Local → Remote** (top-right) before running any control script.

**Note:** keyboard teleoperation requires an **X11** session (Wayland blocks the
global keyboard capture this relies on). Check with `echo $XDG_SESSION_TYPE`.

## Verify the RTDE connection

```bash
python src/rtde_test.py
```

## Record demonstrations

```bash
git clone https://github.com/scy-v/lerobot_ur5e_keyteleop.git third_party/lerobot_ur5e_keyteleop
# see custom_code/ for the modifications applied on top of this repo
# (OpenCV + PyBullet camera backends, added to run_record.py / cfg.yaml)

PYTHONPATH=third_party/_scripts_pathfix \
PATH="venv/bin:$PATH" \
venv/bin/ur5e-record
```

Controls: `w/s`=x, `a/d`=y, `q/e`=z, `r/t g/f b/v`=rotation, `→`=end episode,
`←`=re-record episode, **`Esc`=end session and save (never use Ctrl+C — it can
discard the entire session)**.

## Convert to RLDS

```bash
python rlds_conversion/convert_to_rlds.py <lerobot_dataset_path> <output_name>
python rlds_conversion/validate_rlds.py
```

## Repository structure

```
src/                    RTDE connection test
custom_code/            Custom camera plugins + config modifications
  pybullet_render_camera.py   LeRobot Camera plugin rendering live robot pose
  run_record_MODIFIED.py      Recording script with OpenCV + PyBullet backends added
  cfg.yaml                    Recording configuration
rlds_conversion/        LeRobot → RLDS conversion + validation scripts
RLDS_Target_Schema.pdf  Data schema documentation
```

## Known limitations

- Camera views are synthetic (rendered from the robot's true joint state via
  PyBullet), not from a physical camera mounted on the robot — see
  `RLDS_Target_Schema.pdf` for the full explanation. Real webcam integration was also
  built and tested (OpenCV backend) and can be re-enabled if needed.
- `reward` is a placeholder (`0.0`) — this is a pure imitation-learning dataset, no
  reward signal is computed.
