"""Setup script for Query Tuner Tool."""

from setuptools import setup, find_packages

setup(
    name="query-tuner-tool",
    version="0.1.0",
    packages=find_packages(exclude=["tests*"]),
    python_requires=">=3.11",
    install_requires=[
        # Read from requirements/base.txt
    ],
    extras_require={
        "dev": [
            # Read from requirements/dev.txt
        ],
        "test": [
            # Read from requirements/test.txt
        ],
    },
)
