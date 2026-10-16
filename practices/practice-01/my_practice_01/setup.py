from setuptools import find_packages, setup

package_name = 'my_practice_01'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/digitDrawer.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='fedia',
    maintainer_email='fedia@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'turtle_digit_drawer = my_practice_01.turtle_digit_drawer:main'
        ],
    },
    
)
