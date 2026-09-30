from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction
from launch_ros.actions import Node


def generate_launch_description():
    turtlesim_node = Node(
        package='turtlesim',
        executable='turtlesim_node',
        name='turtlesim',
    )

    spawn_turtle2 = TimerAction(
        period=1.0,
        actions=[
            ExecuteProcess(
                cmd=[
                    'ros2', 'service', 'call', '/spawn',
                    'turtlesim/srv/Spawn',
                    "{x: 8.0, y: 5.5, theta: 0.0, name: 'turtle2'}",
                ],
                output='screen',
            )
        ],
    )

    draw_digit_1 = TimerAction(
        period=2.0,
        actions=[
            Node(
                package='my_practice_01',
                executable='turtle_digit_drawer',
                name='draw_digit_1',
                parameters=[{'turtle_name': 'turtle1', 'digit': 1}],
            )
        ],
    )

    draw_digit_7 = TimerAction(
        period=2.0,
        actions=[
            Node(
                package='my_practice_01',
                executable='turtle_digit_drawer',
                name='draw_digit_7',
                parameters=[{'turtle_name': 'turtle2', 'digit': 7}],
            )
        ],
    )

    return LaunchDescription([
        turtlesim_node,
        spawn_turtle2,
        draw_digit_1,
        draw_digit_7,
    ])