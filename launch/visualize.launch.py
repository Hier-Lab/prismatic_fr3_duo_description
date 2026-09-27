"""Visualize the prismatic FR3 duo with interactive joint sliders."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import (
    Command,
    FindExecutable,
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    """Create the robot publishers, joint GUI, and RViz launch description."""
    package_share = FindPackageShare("prismatic_fr3_duo_description")

    # Keep model, configuration, and RViz paths replaceable from the command line.
    default_xacro = PathJoinSubstitution(
        [package_share, "urdf", "prismatic_fr3_duo.urdf.xacro"]
    )
    default_config = PathJoinSubstitution(
        [package_share, "config", "prismatic_fr3_duo.yaml"]
    )
    default_rviz = PathJoinSubstitution(
        [package_share, "rviz", "prismatic_fr3_duo.rviz"]
    )

    xacro_file = LaunchConfiguration("xacro_file")
    config_file = LaunchConfiguration("config_file")
    use_sim_time = ParameterValue(
        LaunchConfiguration("use_sim_time"), value_type=bool
    )

    # Xacro output is supplied directly to robot_state_publisher as XML text.
    robot_description = ParameterValue(
        Command(
            [
                FindExecutable(name="xacro"),
                " ",
                xacro_file,
                " config_file:=",
                config_file,
            ]
        ),
        value_type=str,
    )

    arguments = [
        DeclareLaunchArgument("xacro_file", default_value=default_xacro),
        DeclareLaunchArgument("config_file", default_value=default_config),
        DeclareLaunchArgument("rviz_config", default_value=default_rviz),
        DeclareLaunchArgument(
            "use_gui",
            default_value="true",
            description="Start joint_state_publisher_gui.",
        ),
        DeclareLaunchArgument(
            "use_rviz", default_value="true", description="Start RViz2."
        ),
        DeclareLaunchArgument(
            "use_sim_time", default_value="false", description="Use simulation time."
        ),
    ]

    # Publish the URDF transforms from joint states selected in the GUI.
    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[
            {"robot_description": robot_description, "use_sim_time": use_sim_time}
        ],
    )
    joint_state_publisher_gui = Node(
        package="joint_state_publisher_gui",
        executable="joint_state_publisher_gui",
        name="joint_state_publisher_gui",
        output="screen",
        condition=IfCondition(LaunchConfiguration("use_gui")),
    )
    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", LaunchConfiguration("rviz_config")],
        parameters=[{"use_sim_time": use_sim_time}],
        condition=IfCondition(LaunchConfiguration("use_rviz")),
    )

    return LaunchDescription(
        [*arguments, robot_state_publisher, joint_state_publisher_gui, rviz]
    )
