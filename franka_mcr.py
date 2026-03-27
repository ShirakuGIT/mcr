import pybullet as p
import pybullet_data
import time
import numpy as np

def create_tabletop_scene():
    client_id = p.connect(p.GUI)
    p.configureDebugVisualizer(p.COV_ENABLE_GUI, 0)

    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    p.setGravity(0, 0, -9.81)

    p.loadURDF("plane.urdf")
    p.loadURDF("table/table.urdf", basePosition=[0, 0, 0])

    robot_start_pos = [0, -0.4, 0.625]
    robot_start_orientation = p.getQuaternionFromEuler([0, 0, 0])

    robot_id = p.loadURDF(
        "franka_panda/panda.urdf",
        basePosition=robot_start_pos,
        baseOrientation=robot_start_orientation,
        useFixedBase=True,
        flags=p.URDF_USE_SELF_COLLISION
    )

    # Add mild damping to stabilize solver impulses
    for j in range(p.getNumJoints(robot_id)):
        p.changeDynamics(robot_id, j,
                         linearDamping=0.04,
                         angularDamping=0.04)

    obstacle_id = p.loadURDF(
        "cube_small.urdf",
        basePosition=[0, 0.3, 0.65]
    )
    p.changeDynamics(obstacle_id, -1, mass=0)

    return client_id, robot_id


# Joint utilities

def get_revolute_joint_indices(robot_id):
    indices = []
    print("Robot Joint Info:")

    for i in range(p.getNumJoints(robot_id)):
        info = p.getJointInfo(robot_id, i)
        if info[2] == p.JOINT_REVOLUTE:
            indices.append(i)
            print(f"  Joint {i}: {info[1].decode('utf-8')}")

    return indices


def get_joint_limits(robot_id, joint_indices):
    lower = []
    upper = []

    for i in joint_indices:
        info = p.getJointInfo(robot_id, i)
        lower.append(info[8])
        upper.append(info[9])

    return np.array(lower), np.array(upper)


def get_current_configuration(robot_id, joint_indices):
    return np.array([
        p.getJointState(robot_id, i)[0]
        for i in joint_indices
    ])


def set_configuration(robot_id, joint_indices, target):
    p.setJointMotorControlArray(
        bodyUniqueId=robot_id,
        jointIndices=joint_indices,
        controlMode=p.POSITION_CONTROL,
        targetPositions=target,
        forces=[120.0] * len(joint_indices)
    )


# Random walk

def main():
    print("Initializing PyBullet Tabletop Scene...")
    client_id, robot_id = create_tabletop_scene()

    p.resetDebugVisualizerCamera(
        cameraDistance=1.5,
        cameraYaw=45,
        cameraPitch=-30,
        cameraTargetPosition=[0, 0, 0.5]
    )

    joint_indices = get_revolute_joint_indices(robot_id)
    lower_limits, upper_limits = get_joint_limits(robot_id, joint_indices)

    num_dof = len(joint_indices)
    print(f"\nRobot has {num_dof} DoF.")

    print("\nStarting stable random walk in C-space...")

    try:
        for step in range(10000):

            if step % 60 == 0:
                # Read actual current state (prevents drift)
                q_current = get_current_configuration(robot_id, joint_indices)

                # Small incremental step
                delta = np.random.uniform(-0.04, 0.04, num_dof)
                q_target = q_current + delta

                # Clamp to physical limits
                q_target = np.clip(q_target, lower_limits, upper_limits)

                set_configuration(robot_id, joint_indices, q_target)

            p.stepSimulation()
            time.sleep(1.0 / 240.0)

    except KeyboardInterrupt:
        print("Simulation stopped.")

    p.disconnect(client_id)
    print("Finished.")


if __name__ == "__main__":
    main()