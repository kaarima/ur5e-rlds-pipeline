#!/usr/bin/env python3
"""Read the live joint state and TCP pose from a UR robot over RTDE."""

import argparse
import sys

from rtde_receive import RTDEReceiveInterface


DEFAULT_ROBOT_HOST = "127.0.0.1"
RTDE_PORT = 30004


def format_vector(values: list[float]) -> str:
    """Format robot state vectors with stable, readable precision."""
    return "[" + ", ".join(f"{value:.6f}" for value in values) + "]"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Print the current joint positions and TCP pose over RTDE."
    )
    parser.add_argument("--host", default=DEFAULT_ROBOT_HOST, help="Robot host or IP")
    args = parser.parse_args()

    rtde_receive = None
    try:
        rtde_receive = RTDEReceiveInterface(args.host)
        if not rtde_receive.isConnected():
            raise ConnectionError("RTDE interface did not establish a connection")

        joint_positions = rtde_receive.getActualQ()
        tcp_pose = rtde_receive.getActualTCPPose()
    except Exception as error:
        print(
            f"Could not connect to URSim at {args.host} over RTDE: {error}",
            file=sys.stderr,
        )
        print(
            "Check that URSim is running, the robot is powered on and running, "
            f"and RTDE port {RTDE_PORT} is published to {args.host}.",
            file=sys.stderr,
        )
        return 1
    finally:
        if rtde_receive is not None:
            rtde_receive.disconnect()

    print(f"Joint positions (rad): {format_vector(joint_positions)}")
    print(f"TCP pose (m, rad):     {format_vector(tcp_pose)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
