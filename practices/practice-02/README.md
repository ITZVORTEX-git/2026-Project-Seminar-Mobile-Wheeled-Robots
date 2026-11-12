инструкция по сборке:
cd ~/practices_ws
colcon build --symlink-install --packages-select my_practice_02
source install/setup.zsh

запуск:
ros2 launch my_practice_02 circle.launch.py