"""Setup configuration for lego_sorter package."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="lego_sorter",
    version="0.1.0",
    author="Andrew J Lockhart",
    description="Code to hold state of Lego Sorter Buckets",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AndrewJLockhart/LegoSorterAlgo",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
