"""
A synthetic camera for LeRobot that renders the UR5e's actual current pose
using PyBullet, instead of capturing from a physical camera.

This class mimics the same interface LeRobot's other camera classes use
(connect / read / disconnect), so it can be swapped in wherever a real
camera would normally go.

It maintains its OWN separate RTDE connection to read the robot's live
joint angles - it does not depend on the main robot object passing data
to it, which keeps it self-contained and simple to plug in.
"""

import numpy as np
import pybullet as p
import rtde_receive


class PyBulletRenderCamera:
    def __init__(self, robot_ip: str, urdf_path: str, fps: int = 30,
                 width: int = 640, height: int = 480,
                 camera_eye=(1.2, 1.2, 1.0), camera_target=(0, 0, 0.3)):
        self.robot_ip = robot_ip
        self.urdf_path = urdf_path
        self.fps = fps
        self.width = width
        self.height = height
        self.camera_eye = camera_eye
        self.camera_target = camera_target

        self._physics_client = None
        self._robot_body_id = None
        self._movable_joint_indices = None
        self._rtde_r = None
        self._view_matrix = None
        self._proj_matrix = None
        self._is_connected = False

    def connect(self):
        # Start our own physics simulation, headless (no GUI window)
        self._physics_client = p.connect(p.DIRECT)
        self._robot_body_id = p.loadURDF(self.urdf_path, useFixedBase=True)

        # Find the real revolute (movable) joints, skip fixed ones
        self._movable_joint_indices = []
        for i in range(p.getNumJoints(self._robot_body_id)):
            info = p.getJointInfo(self._robot_body_id, i)
            if info[2] == p.JOINT_REVOLUTE:
                self._movable_joint_indices.append(i)

        if len(self._movable_joint_indices) < 6:
            raise RuntimeError(
                f"Expected at least 6 revolute joints, found "
                f"{len(self._movable_joint_indices)}. URDF may be wrong."
            )

        # Set up a fixed camera viewpoint looking at the robot
        self._view_matrix = p.computeViewMatrix(
            cameraEyePosition=list(self.camera_eye),
            cameraTargetPosition=list(self.camera_target),
            cameraUpVector=[0, 0, 1],
        )
        self._proj_matrix = p.computeProjectionMatrixFOV(
            fov=60, aspect=self.width / self.height, nearVal=0.1, farVal=5.0
        )

        # Connect to the robot's real joint state via RTDE
        self._rtde_r = rtde_receive.RTDEReceiveInterface(self.robot_ip)

        self._is_connected = True

    def read(self) -> np.ndarray:
        if not self._is_connected:
            raise RuntimeError("PyBulletRenderCamera is not connected. Call connect() first.")

        # Get the robot's real current joint angles
        actual_q = self._rtde_r.getActualQ()

        # Apply them to our simulated robot model
        for idx, angle in zip(self._movable_joint_indices[:6], actual_q):
            p.resetJointState(self._robot_body_id, idx, angle)

        # Render an image from this exact pose
        _, _, rgb_img, _, _ = p.getCameraImage(
            width=self.width,
            height=self.height,
            viewMatrix=self._view_matrix,
            projectionMatrix=self._proj_matrix,
            renderer=p.ER_TINY_RENDERER,
        )

        rgb_array = np.array(rgb_img, dtype=np.uint8).reshape(self.height, self.width, 4)
        return rgb_array[:, :, :3]  # drop alpha channel, keep RGB

    def disconnect(self):
        if self._rtde_r is not None:
            self._rtde_r.disconnect()
        if self._physics_client is not None:
            p.disconnect(self._physics_client)
        self._is_connected = False
