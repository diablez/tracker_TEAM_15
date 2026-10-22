import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'path_planner_server_TEAM_15'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.xml')),
        (os.path.join('share', package_name, 'config'), glob('config/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='TEAM_15',
    maintainer_email='team15@example.com',
    description='Team 15 physical and simulated Nav2 launch configuration.',
    license='LicenseRef-Team15-Pending',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
        ],
    },
)
