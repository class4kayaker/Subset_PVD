"""
A utility to package subsets of large ASPECT PVD files to visualize elsewhere
without access to the original filesystem.
"""

from setuptools import find_packages, setup

version = '0.1.0'
dependencies = ['click']

setup(
    name='subsetPVD',
    version=version,
    packages=find_packages(),
    install_requires=dependencies,
    entry_points={
        'console_scripts': [
            'gen_pvd_subset = subsetPVD.cli:create_subset_archive'
        ]
    }
)
