import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    package_dir = get_package_share_directory('my_practice_02')

    linear = LaunchConfiguration('linear')
    angular = LaunchConfiguration('angular')
    delay = LaunchConfiguration('delay')

    scene = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(package_dir, 'launch', 'robot.launch.py')),
        launch_arguments={'mode': LaunchConfiguration('mode')}.items(),
    )

    drive = ExecuteProcess(
        cmd=[
            'ros2', 'topic', 'pub', '-r', '10', '/cmd_vel',
            'geometry_msgs/msg/TwistStamped',
            ['{header: {frame_id: base_link}, twist: {linear: {x: ', linear,
             '}, angular: {z: ', angular, '}}}'],
        ],
        output='screen',
    )

    return LaunchDescription([
        DeclareLaunchArgument('linear', default_value='0.19',
                              description='Linear velocity, m/s'),
        DeclareLaunchArgument('angular', default_value='0.1',
                              description='Angular velocity, rad/s'),
        DeclareLaunchArgument('delay', default_value='5.0',
                              description='Seconds to wait before publishing /cmd_vel'),
        DeclareLaunchArgument('mode', default_value='realtime',
                              description='Webots startup mode'),
        scene,
        TimerAction(period=delay, actions=[drive]),
    ])
