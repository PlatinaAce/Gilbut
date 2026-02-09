from setuptools import setup
import os
from glob import glob

package_name = 'llm_goal_bridge'

setup(
    name=package_name,
    version='0.0.2',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name), [os.path.join(package_name, 'place_db.yaml')]),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='you',
    maintainer_email='you@example.com',
    description='TCP(JSONL) to Nav2 goal bridge for LLM voice commands (with optional cmd_vel)',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'tcp_goal_bridge = llm_goal_bridge.tcp_goal_bridge:main',
        ],
    },
)
