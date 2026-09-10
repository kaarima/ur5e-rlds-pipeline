import pybullet as p
import pybullet_data
import numpy as np
from PIL import Image

# Connect headless (no GUI window needed on a remote/server machine)
physics_client = p.connect(p.DIRECT)

# Load the URDF
urdf_path = "/home/karima/Documents/ur5e_rlds_project/third_party/ur5e_model/ur5e.urdf"
robot_id = p.loadURDF(urdf_path, useFixedBase=True)

print(f"Loaded robot with {p.getNumJoints(robot_id)} joints.")

# Use the SAME joint positions you saw from your real RTDE test earlier,
# so this is directly comparable to your actual recorded data.
test_joint_positions = [-1.6007, -1.7271, -2.203, -0.808, 1.5951, -0.031]

# Find the actual revolute (movable) joints - URDF files often include
# fixed joints too, which we should skip.
movable_joint_indices = []
for i in range(p.getNumJoints(robot_id)):
    info = p.getJointInfo(robot_id, i)
    joint_type = info[2]
    if joint_type == p.JOINT_REVOLUTE:
        movable_joint_indices.append(i)

print(f"Found {len(movable_joint_indices)} revolute joints: {movable_joint_indices}")

# Set the first 6 revolute joints to our test pose
for idx, angle in zip(movable_joint_indices[:6], test_joint_positions):
    p.resetJointState(robot_id, idx, angle)

# Set up a camera looking at the robot
view_matrix = p.computeViewMatrix(
    cameraEyePosition=[1.2, 1.2, 1.0],
    cameraTargetPosition=[0, 0, 0.3],
    cameraUpVector=[0, 0, 1],
)
proj_matrix = p.computeProjectionMatrixFOV(
    fov=60, aspect=640 / 480, nearVal=0.1, farVal=5.0
)

width, height, rgb_img, depth_img, seg_img = p.getCameraImage(
    width=640,
    height=480,
    viewMatrix=view_matrix,
    projectionMatrix=proj_matrix,
    renderer=p.ER_TINY_RENDERER,  # software renderer, works headless without a GPU
)

# Convert to a proper image and save
rgb_array = np.array(rgb_img, dtype=np.uint8).reshape(height, width, 4)[:, :, :3]
img = Image.fromarray(rgb_array)
img.save("/home/karima/pybullet_render_test.png")

print("Saved rendered image to ~/pybullet_render_test.png")
p.disconnect()
