#!/usr/bin/env python3
"""Setup script for TISM package"""

from setuptools import setup, find_packages
import os

# Read README
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="tism-framework",
    version="1.0.0",
    author="Mathew Moslow",
    author_email="",
    description="Think In Stacks Method (TISM) - A validated framework for nursing clinical decision-making",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Mathewmoslow/thinkinstacksmethod",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Education",
        "Intended Audience :: Healthcare Industry",
        "Topic :: Education",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "python-dotenv>=1.0.0",
        "colorama>=0.4.6",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "scipy>=1.10.0",
    ],
    extras_require={
        "ai": ["openai>=0.27.0"],
        "viz": ["matplotlib>=3.7.0", "seaborn>=0.12.0"],
        "dev": ["pytest>=7.0.0", "pytest-cov>=4.0.0"],
    },
    entry_points={
        "console_scripts": [
            "tism=core.tism_tree_final:main",
            "tism-validate=validation.extract_and_test_priority_questions:main",
        ],
    },
    include_package_data=True,
    package_data={
        "data": ["*.json", "*.db"],
    },
)