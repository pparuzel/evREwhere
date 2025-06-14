"""Setup script for the evre package."""

from setuptools import find_packages, setup

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="evre",
    version="0.1.0",
    packages=find_packages(),
    py_modules=["evre"],
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "evre = evre:main",
        ],
    },
)
