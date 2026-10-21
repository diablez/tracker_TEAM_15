from setuptools import find_packages, setup
from glob import glob
import os

package_name = 'tracker_TEAM_15'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='TEAM_15',
    maintainer_email='team15@example.com',
    description='TEAM15 TF/Nav2 pursuit and compressed RGB capture reporting',
    license='LicenseRef-Team15-Pending',
    entry_points={'console_scripts': [
        'tracker_two_tb4_TEAM_15 = tracker_TEAM_15.tracker_two_tb4_TEAM_15:main',
        'tracker_node = tracker_TEAM_15.tracker_node:main',
        'tracker_tb3_sim_TEAM_15 = tracker_TEAM_15.tracker_tb3_sim_TEAM_15:main',
        'capture_report = tracker_TEAM_15.capture_report:main',
    ]},
)
