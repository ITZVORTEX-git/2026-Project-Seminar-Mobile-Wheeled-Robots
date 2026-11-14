from setuptools import find_packages, setup
from glob import glob
import os

package_name = "my_practice_04"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (
            os.path.join("share", package_name, "launch"),
            glob(os.path.join("launch", "*launch.[pxy][yma]*")),
        ),
        (
            os.path.join("share", package_name, "worlds"),
            glob(os.path.join("worlds", "*.wbt")),
        ),
        (
            os.path.join("share", package_name, "protos"),
            glob(os.path.join("protos", "*.proto")),
        ),
        (
            os.path.join("share", package_name, "maps"),
            glob('maps/*.png') + glob(os.path.join("maps", "*.pgm")) + glob(os.path.join("maps", "*.yaml")),
        ),
        (
            os.path.join("share", package_name, "config"),
            glob(os.path.join("config", "*.yaml")),
        ),
        (
            os.path.join("share", package_name, "urdf"),
            glob(os.path.join("urdf", "*.urdf")),
        ),
        (
            os.path.join("share", package_name, "rviz"),
            glob(os.path.join("rviz", "*.rviz")),
        ),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Fedor",
    maintainer_email="fdchentsov@edu.hse.ru",
    description="AMCL localization error research",
    license="Apache-2.0",
    extras_require={
        "test": [
            "pytest",
        ],
    },
    entry_points={
        "console_scripts": [
        ],
    },
)
