import wpilib
import wpilib.kinematics
from wpimath.geometry import Rotation2d
import ctre
import commands2 as commands

import utils.logger as logger
from utils.math import sensor_units_to_meters

import sensors
from utils.network import Network


class Drivetrain(commands.SubsystemBase):
    def __init__(self, sim: bool = False) -> None:
        super().__init__()

        if sim:
            return

        logger.info("initializing drivetrain", "[drivetrain]")

        self.left2 = ctre.TalonFX(0)
        self.left1 = ctre.TalonFX(1)
        self.left3 = ctre.TalonFX(2)
        self.right2 = ctre.TalonFX(3)
        self.right1 = ctre.TalonFX(4)
        self.right3 = ctre.TalonFX(5)

        self.origin_x = 0
        self.origin_y = 0
        self.origin_theta = Rotation2d(0)

        self.flipped = False

        logger.info("configuring odometry", "[drivetrain.odometry]")

        self.gyro = sensors.Gyro()
        self.gyro.reset()
        self.odometry = wpilib.kinematics.DifferentialDriveOdometry(Rotation2d(0))

        self.reset_pose()

        logger.info("initialization complete", "[drivetrain]")

    def set_motor_percent_output(self, left: float, right: float):
        if self.flipped:
            left, right = right, left
        self.left1.set(ctre.ControlMode.PercentOutput, left)
        self.right1.set(ctre.ControlMode.PercentOutput, right)

    def set_motor_velocity(self, left: float, right: float):
        if self.flipped:
            left, right = right, left
        self.left1.set(ctre.ControlMode.Velocity, left)
        self.right1.set(ctre.ControlMode.Velocity, right)

    def reset_pose(self, flipped: bool = False):
        logger.info(f"resetting pose{' (flipped)' if flipped else ''}....")
        self.flipped = flipped
        self.gyro.reset(0)
        self.odometry = wpilib.kinematics.DifferentialDriveOdometry(Rotation2d(0))
        self.left1.setSelectedSensorPosition(0)
        self.right1.setSelectedSensorPosition(0)

    def get_pose(self):
        return self.odometry.getPose()

    def periodic(self) -> None:
        self.update_odometry()
        pose = self.get_pose()
        Network.test_table.putNumber("pose_x", pose.X())
        Network.test_table.putNumber("pose_y", pose.Y())
        Network.test_table.putNumber("pose_degrees", pose.rotation().degrees())

    def update_odometry(self):
        left = sensor_units_to_meters(-self.left1.getSelectedSensorPosition(), True)
        right = sensor_units_to_meters(self.right1.getSelectedSensorPosition(), True)
        if self.flipped:
            left, right = right, left
        self.odometry.update(Rotation2d(-self.gyro.heading * 0.0174533).rotateBy(self.rotation_offset), left, right)

    def config_motors(self):
        logger.info("configuring motor closed loop", "[drivetrain.motor]")

        self.left1.config_kF(0, 1023.0 / 20132.0)
        self.right1.config_kF(0, 1023.0 / 20162.0)

        def _config_pid(motor: ctre.TalonFX):
            motor.config_kP(1, 0.5)
            motor.config_kI(1, 0.0)
            motor.config_kD(1, 0.0)
            motor.configClosedLoopPeakOutput(1, 1.0)
            motor.configMotionCruiseVelocity(15000)
            motor.configMotionAcceleration(10000)

        _config_pid(self.left1)
        _config_pid(self.right1)

        self.left2.follow(self.left1)
        self.left3.follow(self.left1)
        self.right2.follow(self.right1)
        self.right3.follow(self.right1)
