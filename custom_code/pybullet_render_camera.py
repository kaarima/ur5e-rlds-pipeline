"""A synthetic camera that renders the UR5e's live pose via PyBullet,
instead of capturing from physical camera hardware. Mirrors the structure
of dummy_camera.py in this same package.
"""

from dataclasses import dataclass, field
from typing import Any

import numpy as np
from numpy.typing import NDArray

from lerobot.cameras import Camera, CameraConfig, ColorMode
from lerobot.utils.errors import DeviceAlreadyConnectedError, DeviceNotConnectedError


@CameraConfig.register_subclass("ur5e_pybullet_render")
@dataclass(kw_only=True)
class PyBulletCameraConfig(CameraConfig):
    robot_ip: str = "127.0.0.1"
    urdf_path: str = ""
    camera_eye: tuple = (1.2, 1.2, 1.0)
    camera_target: tuple = (0, 0, 0.3)

    def __post_init__(self) -> None:
        if self.fps is None or self.width is None or self.height is None:
            raise ValueError("PyBulletCamera requires fps, width, and height.")
        if self.fps <= 0 or self.width <= 0 or self.height <= 0:
            raise ValueError("PyBulletCamera fps, width, and height must be positive.")
        if not self.urdf_path:
            raise ValueError("PyBulletCamera requires a urdf_path.")


class PyBulletCamera(Camera):
    """LeRobot camera implementation that renders the robot's live pose
    (read via its own RTDE connection) using PyBullet, instead of reading
    from physical camera hardware."""

    def __init__(self, config: PyBulletCameraConfig):
        super().__init__(config)
        self.config = config
        self._is_connected = False
        self._physics_client = None
        self._robot_body_id = None
        self._movable_joint_indices = None
        self._rtde_r = None
        self._view_matrix = None
        self._proj_matrix = None

    def __str__(self) -> str:
        return f"PyBulletCamera({self.width}x{self.height})"

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    @staticmethod
    def find_cameras() -> list[dict[str, Any]]:
        return []

    def connect(self, warmup: bool = True) -> None:
        if self.is_connected:
            raise DeviceAlreadyConnectedError(f"{self} is already connected.")

        import pybullet as p
        import rtde_receive

        self._physics_client = p.connect(p.DIRECT)
        self._robot_body_id = p.loadURDF(self.config.urdf_path, useFixedBase=True)

        self._movable_joint_indices = []
        for i in range(p.getNumJoints(self._robot_body_id)):
            info = p.getJointInfo(self._robot_body_id, i)
            if info[2] == p.JOINT_REVOLUTE:
                self._movable_joint_indices.append(i)

        if len(self._movable_joint_indices) < 6:
            raise RuntimeError(
                f"{self}: expected at least 6 revolute joints, found "
                f"{len(self._movable_joint_indices)}."
            )

        self._view_matrix = p.computeViewMatrix(
            cameraEyePosition=list(self.config.camera_eye),
            cameraTargetPosition=list(self.config.camera_target),
            cameraUpVector=[0, 0, 1],
        )
        self._proj_matrix = p.computeProjectionMatrixFOV(
            fov=60, aspect=self.width / self.height, nearVal=0.1, farVal=5.0
        )

        self._rtde_r = rtde_receive.RTDEReceiveInterface(self.config.robot_ip)
        self._is_connected = True

    def read(self, color_mode: ColorMode | None = None) -> NDArray[Any]:
        if not self.is_connected:
            raise DeviceNotConnectedError(f"{self} is not connected.")

        import pybullet as p

        actual_q = self._rtde_r.getActualQ()
        for idx, angle in zip(self._movable_joint_indices[:6], actual_q):
            p.resetJointState(self._robot_body_id, idx, angle)

        _, _, rgb_img, _, _ = p.getCameraImage(
            width=self.width,
            height=self.height,
            viewMatrix=self._view_matrix,
            projectionMatrix=self._proj_matrix,
            renderer=p.ER_TINY_RENDERER,
        )
        rgb_array = np.array(rgb_img, dtype=np.uint8).reshape(self.height, self.width, 4)
        return rgb_array[:, :, :3].copy()

    def async_read(self, timeout_ms: float = 200) -> NDArray[Any]:
        return self.read()

    def disconnect(self) -> None:
        if not self.is_connected:
            raise DeviceNotConnectedError(f"{self} is not connected.")

        import pybullet as p

        if self._rtde_r is not None:
            self._rtde_r.disconnect()
        if self._physics_client is not None:
            p.disconnect(self._physics_client)
        self._is_connected = False
