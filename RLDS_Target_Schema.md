# Target RLDS Dataset Schema

**Source data:** LeRobot dataset collected via keyboard teleoperation of a simulated
UR5e (URSim), recorded at 30 fps, with two synthetic camera viewpoints (see Section 2.1).

This document describes how the recorded LeRobot data will be mapped into RLDS's
episode/step structure, per Section 3.5 of the task description.

---

## 1. Episode Structure

Each **episode** = one continuous teleoperated demonstration, bounded by the recorder's
own episode start/reset markers.

| RLDS field | Source | Notes |
|---|---|---|
| Episode boundary | LeRobot `episode_index` | Varies per recording session |
| `is_first` | Derived: `frame_index == 0` within an episode | First frame of each episode |
| `is_last` | Derived: last `frame_index` within an episode | Last frame before reset |
| `is_terminal` | Same as `is_last` for this dataset | No distinct "failure" vs. "success" termination is tracked — teleop episodes end on user reset, not task completion |
| Episode metadata | `task_index` → task description string | Currently a single task ("test_name"); real task descriptions will be added when meaningful demonstrations are collected |

## 2. Step Structure

Each **step** = one recorded frame (15 fps), containing a synchronized observation,
action, and timestamp.

### 2.1 `observation`

| Field | Source (LeRobot) | Shape / dtype | Notes |
|---|---|---|---|
| `robot_state` | `observation.state` | `float32[48]` | See breakdown below |
| `image_wrist` | `observation.images.wrist_image` | `uint8[480, 640, 3]` | **Synthetic rendered view** (PyBullet), viewpoint A — see note below |
| `image_exterior` | `observation.images.exterior_image` | `uint8[480, 640, 3]` | **Synthetic rendered view** (PyBullet), viewpoint B — see note below |

**Important naming note:** despite the field names `wrist_image`/`exterior_image` (LeRobot's standard
naming convention), **neither stream is a first-person view from a camera mounted on the robot.**
Both are external, fixed-position synthetic viewpoints rendered by PyBullet from the robot's true
joint state (read live via RTDE each frame) — effectively two "security camera" angles watching the
simulated robot, from two different fixed positions/orientations, not two robot-mounted cameras
looking outward. This was a deliberate choice given the hardware constraint of one physical webcam
(insufficient for two genuinely different real feeds) combined with the task's stated optional
alternative (Section 3.3): rendering images directly from joint angles via a
physics/kinematics library. Both configured views are accurate to the robot's real pose at every
frame; they are not placeholders.

**`observation.state` (48-dim) breakdown:**

| Sub-field | Dims | Description |
|---|---|---|
| `tcp_pose` | 6 | End-effector pose: x, y, z, rx, ry, rz |
| `tcp_speed` | 6 | End-effector velocity |
| `tcp_force` | 6 | Force/torque at end-effector |
| `tcp_acc` | 3 | End-effector linear acceleration (x, y, z) |
| `gripper` | 3 | `raw_position`, `raw_bin`, `action_bin` |
| `joint.pos` | 6 | Joint positions (rad), one per UR5e joint |
| `joint.vel` | 6 | Joint velocities |
| `joint.acc` | 6 | Joint accelerations |
| `joint.force` | 6 | Joint torques |

### 2.2 `action`

| Field | Source | Shape / dtype | Notes |
|---|---|---|---|
| `action` | `action` | `float32[6]` | Cartesian delta command: `delta_x, delta_y, delta_z, delta_rx, delta_ry, delta_rz` — the keyboard-teleop step deltas sent to the robot each control cycle |

### 2.3 `reward`

Not used. This is a pure imitation-learning data collection task; no reward signal is
computed or stored. RLDS's `reward` field will be omitted or set to `0.0` as a placeholder
if the schema requires it structurally.

### 2.4 Per-step metadata

| Field | Source | Notes |
|---|---|---|
| `timestamp` | `timestamp` | Float seconds, used for synchronization verification |
| `frame_index` | `frame_index` | Frame position within its episode |
| `episode_index` | `episode_index` | Which episode this step belongs to |
| `global_index` | `index` | Global frame index across the whole dataset |
| `task_index` | `task_index` | Maps to the task description string (language instruction, if/when used) |

---

## 3. Synchronization Notes (Section 3.9)

- **Robot control rate:** RTDE state reads occur at the robot's native control frequency; teleop steps are logged at the dataset's fixed **30 fps** (raised from an initial 15 fps to match the physical webcam tested during development; the current PyBullet-rendered dataset keeps the same rate for consistency).
- **Camera frame rate:** Both rendered views are generated on-demand each frame by querying the robot's live joint state via RTDE and rendering fresh — so they are inherently synchronized to the logging loop's rate (30 fps) with no independent camera clock to drift out of sync.
- **Timestamp generation:** Each step's `timestamp` is recorded at the moment the frame is logged by the LeRobot recording loop, alongside the corresponding robot state read and action command — all three are captured within the same loop iteration, ensuring per-step alignment by construction rather than post-hoc matching.
- **Missing/delayed frames:** Not applicable to the current PyBullet-rendered setup — rendering from live joint state cannot "miss a frame" the way a physical camera read can. This section would need revisiting if a physical webcam or RealSense camera is reintroduced later (a real webcam was tested during development and did work, but was ultimately not used for the current dataset in favor of the dual-rendered approach).

---

## 4. Open Questions for Bahaeddine

- The current dataset uses two **synthetic rendered** camera views (not a physical webcam) — see the naming note in Section 2.1. Is this acceptable for the intended use of this dataset, or is at least one real-world image stream required? A physical webcam integration was tested successfully during development and can be reintroduced if preferred.
- Is a placeholder `reward = 0.0` needed for RLDS/TFDS tooling compatibility, or can the field be omitted entirely?
- Should `is_terminal` distinguish "task completed" from "manually reset," or is treating every episode end as terminal acceptable for this dataset's purpose?
