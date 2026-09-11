"""
Converts a recorded LeRobot dataset into RLDS format (built on TFDS).

Usage:
    python convert_to_rlds.py <lerobot_dataset_path> <output_name>

Example:
    python convert_to_rlds.py \
        ~/.cache/huggingface/lerobot/scylearning/test_name_20260910_v10 \
        ur5e_pybullet_demo
"""

import sys
from pathlib import Path

import numpy as np
import tensorflow as tf
import tensorflow_datasets as tfds


def build_rlds_dataset(lerobot_dataset_path: str, output_name: str, data_dir: str):
    from lerobot.datasets.lerobot_dataset import LeRobotDataset

    lerobot_dataset_path = Path(lerobot_dataset_path)

    # LeRobotDataset expects `root` to point DIRECTLY at the dataset folder
    # (the one containing meta/, data/, videos/) - not its parent.
    repo_id = lerobot_dataset_path.name
    root = lerobot_dataset_path

    print(f"Loading LeRobot dataset: repo_id={repo_id}, root={root}")
    lerobot_ds = LeRobotDataset(repo_id=repo_id, root=root)

    print(f"Loaded. {lerobot_ds.num_episodes} episodes, {lerobot_ds.num_frames} total frames.")

    class UR5eRLDSBuilder(tfds.core.GeneratorBasedBuilder):
        VERSION = tfds.core.Version("1.0.0")
        RELEASE_NOTES = {"1.0.0": "Initial conversion from LeRobot dataset."}

        def _info(self) -> tfds.core.DatasetInfo:
            return tfds.core.DatasetInfo(
                builder=self,
                description="UR5e teleoperation demonstrations, converted from LeRobot to RLDS.",
                features=tfds.features.FeaturesDict({
                    "steps": tfds.features.Dataset({
                        "observation": tfds.features.FeaturesDict({
                            "robot_state": tfds.features.Tensor(shape=(48,), dtype=np.float32),
                            "image_wrist": tfds.features.Image(shape=(480, 640, 3)),
                            "image_exterior": tfds.features.Image(shape=(480, 640, 3)),
                        }),
                        "action": tfds.features.Tensor(shape=(6,), dtype=np.float32),
                        "is_first": tf.bool,
                        "is_last": tf.bool,
                        "is_terminal": tf.bool,
                        "reward": tf.float32,
                        "discount": tf.float32,
                        "timestamp": tf.float32,
                    }),
                    "episode_metadata": tfds.features.FeaturesDict({
                        "episode_index": tf.int64,
                        "task_description": tf.string,
                    }),
                }),
            )

        def _split_generators(self, dl_manager):
            return {"train": self._generate_examples()}

        def _generate_examples(self):
            for ep_idx in range(lerobot_ds.num_episodes):
                episode_frame_indices = np.where(
                    np.array(lerobot_ds.hf_dataset["episode_index"]) == ep_idx
                )[0]

                steps = []
                num_frames_in_ep = len(episode_frame_indices)

                for i, frame_idx in enumerate(episode_frame_indices):
                    frame = lerobot_ds[int(frame_idx)]

                    robot_state = frame["observation.state"].numpy().astype(np.float32)
                    action = frame["action"].numpy().astype(np.float32)
                    timestamp = float(frame["timestamp"])

                    # Images come back as CHW float tensors in [0,1] from LeRobotDataset;
                    # convert to HWC uint8 for TFDS's Image feature.
                    img_wrist = (frame["observation.images.wrist_image"].numpy()
                                 .transpose(1, 2, 0) * 255).astype(np.uint8)
                    img_exterior = (frame["observation.images.exterior_image"].numpy()
                                    .transpose(1, 2, 0) * 255).astype(np.uint8)

                    steps.append({
                        "observation": {
                            "robot_state": robot_state,
                            "image_wrist": img_wrist,
                            "image_exterior": img_exterior,
                        },
                        "action": action,
                        "is_first": i == 0,
                        "is_last": i == num_frames_in_ep - 1,
                        "is_terminal": i == num_frames_in_ep - 1,
                        "reward": 0.0,
                        "discount": 1.0,
                        "timestamp": timestamp,
                    })

                yield ep_idx, {
                    "steps": steps,
                    "episode_metadata": {
                        "episode_index": ep_idx,
                        "task_description": "UR5e keyboard teleoperation (test task)",
                    },
                }

    builder = UR5eRLDSBuilder(data_dir=data_dir)
    print(f"Builder name (auto-derived): {builder.name}")
    builder.download_and_prepare()
    print(f"\nDone. RLDS dataset written to: {builder.data_dir}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python convert_to_rlds.py <lerobot_dataset_path> <output_name>")
        sys.exit(1)

    lerobot_path = sys.argv[1]
    output_name = sys.argv[2]
    # Each output gets its own isolated folder, so different source datasets
    # never collide or get silently skipped due to TFDS's caching.
    data_dir = str(Path.home() / "rlds_datasets" / output_name)

    build_rlds_dataset(lerobot_path, output_name, data_dir)