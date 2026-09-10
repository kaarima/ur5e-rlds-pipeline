import sys
sys.path.insert(0, "/home/karima/Documents/ur5e_rlds_project/scripts_local")
from pybullet_render_camera import PyBulletRenderCamera
from PIL import Image

cam = PyBulletRenderCamera(
    robot_ip="127.0.0.1",
    urdf_path="/home/karima/Documents/ur5e_rlds_project/third_party/ur5e_model/ur5e.urdf",
)
cam.connect()
print("Connected. Move the robot in PolyScope now, then press Enter to capture frame 1...")
input()
img1 = cam.read()
Image.fromarray(img1).save("/home/karima/pybullet_frame1.png")
print("Saved frame 1. Move the robot again, then press Enter for frame 2...")
input()
img2 = cam.read()
Image.fromarray(img2).save("/home/karima/pybullet_frame2.png")
print("Saved frame 2.")
cam.disconnect()
