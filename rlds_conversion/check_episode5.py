import numpy as np
import tensorflow_datasets as tfds

DATA_DIR = "/home/karima/rlds_datasets/ur5e_pybullet_full"
BUILDER_NAME = "u_r5e_rlds_builder"

ds = tfds.load(BUILDER_NAME, data_dir=DATA_DIR, split="train")

for ep_idx, episode in enumerate(ds):
    if ep_idx != 5:
        continue

    steps = list(episode["steps"])
    print(f"Episode 5: {len(steps)} steps\n")

    for i, s in enumerate(steps):
        action = s["action"].numpy()
        print(f"  step {i}: action = {np.round(action, 4)}")

    actions_all = np.stack([s["action"].numpy() for s in steps])
    print(f"\nMax absolute action value across episode: {np.abs(actions_all).max():.5f}")
    print(f"Any non-zero action: {np.any(actions_all != 0)}")
    break
