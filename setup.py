#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Package setup."""

from setuptools import find_packages, setup

with open("README.md", mode="r", encoding="utf-8") as readme_file:
    long_description = readme_file.read()

setup(
    name="osman",
    version="0.0.1",
    author="STRV DS Department",
    author_email="datascience.dept@strv.com",
    description="STRV OpenSearch manager.",
    long_description_content_type="text/markdown",
    long_description=long_description,
    packages=find_packages(
        exclude=[
            "tests",
            "scripts",
            ".github",
        ]
    ),
    install_requires=[
        "pytest>=7.1",
        "attrs>=22.1",
        "certifi>=2022.9",
        "charset-normalizer>=2.1",
        "click>=8.1",
        "idna>=3.4",
        "iniconfig>=1.1",
        "opensearch-py>=2.0",
        "packaging>=21.3",
        "parameterized>=0.8.1",
        "pluggy>=1.0",
        "py>=1.11",
        "pyparsing>=3.0",
        "requests>=2.28",
        "tomli>=2.0.",
        "urllib3>=1.26",
        "requests-aws4auth>=1.1",
        "deepdiff>=6.2",
    ],
    python_requires=">=3.8",
    include_package_data=True,
)
