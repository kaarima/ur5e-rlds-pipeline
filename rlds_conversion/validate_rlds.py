"""
Validates a generated RLDS dataset: loads it back, checks structure,
and produces a visual summary of one episode.
"""
from pathlib import Path

import numpy as np
import tensorflow_datasets as tfds
import matplotlib
matplotlib.use("Agg")  # no display needed, just saving files
import matplotlib.pyplot as plt

DATA_DIR = str(Path.home() / "rlds_datasets" / "ur5e_pybullet_full")
BUILDER_NAME = "u_r5e_rlds_builder"

print(f"Loading dataset '{BUILDER_NAME}' from {DATA_DIR}...")
ds, info = tfds.load(BUILDER_NAME, data_dir=DATA_DIR, split="train", with_info=True)

print("\n===== Dataset Info =====")
print(info)

episode_count = 0
total_steps = 0
step_counts = []

first_episode_frames_wrist = []
first_episode_frames_exterior = []
first_episode_actions = []

for episode in ds:
    episode_count += 1
    steps = list(episode["steps"])
    n = len(steps)
    step_counts.append(n)
    total_steps += n

    if episode_count == 1:
        for step in steps:
            first_episode_frames_wrist.append(step["observation"]["image_wrist"].numpy())
            first_episode_frames_exterior.append(step["observation"]["image_exterior"].numpy())
            first_episode_actions.append(step["action"].numpy())

print("\n===== Validation Results =====")
print(f"Total episodes: {episode_count}")
print(f"Total steps: {total_steps}")
print(f"Steps per episode: min={min(step_counts)}, max={max(step_counts)}, avg={np.mean(step_counts):.1f}")
print(f"First episode step count: {len(first_episode_frames_wrist)}")

# Shape/dtype sanity check on the very first step
first_ep = next(iter(ds))
first_step = next(iter(first_ep["steps"]))
print("\n===== First Step Shapes/Dtypes =====")
print(f"robot_state: shape={first_step['observation']['robot_state'].shape}, "
      f"dtype={first_step['observation']['robot_state'].dtype}")
print(f"image_wrist: shape={first_step['observation']['image_wrist'].shape}, "
      f"dtype={first_step['observation']['image_wrist'].dtype}")
print(f"image_exterior: shape={first_step['observation']['image_exterior'].shape}, "
      f"dtype={first_step['observation']['image_exterior'].dtype}")
print(f"action: shape={first_step['action'].shape}, dtype={first_step['action'].dtype}")
print(f"is_first={first_step['is_first'].numpy()}, is_last={first_step['is_last'].numpy()}, "
      f"is_terminal={first_step['is_terminal'].numpy()}")

# ---- Timestamp validation ----
timestamps = np.array([s["timestamp"] for s in
                        [step for step in next(iter(ds))["steps"]]])
diffs = np.diff(timestamps)
is_monotonic = np.all(diffs > 0)
expected_interval = 1.0 / 30.0  # dataset recorded at 30 fps

print("\n===== Timestamp Validation (Episode 1) =====")
print(f"First timestamp: {timestamps[0]:.4f}s, Last timestamp: {timestamps[-1]:.4f}s")
print(f"Monotonically increasing: {is_monotonic}")
print(f"Mean interval between steps: {diffs.mean():.4f}s "
      f"(expected ~{expected_interval:.4f}s at 30fps)")
print(f"Min interval: {diffs.min():.4f}s, Max interval: {diffs.max():.4f}s")
if not is_monotonic:
    print("WARNING: timestamps are NOT strictly increasing — check recording/conversion for issues.")

# ---- Visual summary of episode 1: action trajectory + sampled frames ----
actions = np.array(first_episode_actions)  # shape (N, 6)
n_frames = len(first_episode_frames_exterior)
sample_indices = np.linspace(0, n_frames - 1, min(6, n_frames), dtype=int)

fig, axes = plt.subplots(2, len(sample_indices), figsize=(3 * len(sample_indices), 6))

for col, idx in enumerate(sample_indices):
    axes[0, col].imshow(first_episode_frames_exterior[idx])
    axes[0, col].set_title(f"step {idx}")
    axes[0, col].axis("off")
    axes[1, col].imshow(first_episode_frames_wrist[idx])
    axes[1, col].axis("off")

axes[0, 0].set_ylabel("exterior_image", fontsize=10)
axes[1, 0].set_ylabel("wrist_image", fontsize=10)
plt.tight_layout()
plt.savefig(str(Path.home() / "rlds_episode1_frames.png"), dpi=100)
print("\nSaved frame sequence to ~/rlds_episode1_frames.png")

fig2, ax = plt.subplots(figsize=(10, 5))
labels = ["delta_x", "delta_y", "delta_z", "delta_rx", "delta_ry", "delta_rz"]
for i, label in enumerate(labels):
    ax.plot(actions[:, i], label=label)
ax.set_xlabel("step")
ax.set_ylabel("action value")
ax.set_title("Episode 1 — Action trajectory")
ax.legend()
plt.tight_layout()
plt.savefig(str(Path.home() / "rlds_episode1_trajectory.png"), dpi=100)
print("Saved action trajectory plot to ~/rlds_episode1_trajectory.png")

print("\n===== Validation complete =====")