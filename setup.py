#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Package setup."""
import json

from setuptools import find_packages, setup

with open("README.md", mode="r", encoding="utf-8") as readme_file:
    long_description = readme_file.read()

with open("package.json", mode="r", encoding="utf-8") as package_file:
    package_info = package_file.read()
package_info = json.loads(package_info)

setup(
    name=package_info["name"],
    version=package_info["version"],
    author=package_info["author"],
    author_email=package_info["email"],
    url=package_info["url"],
    description=package_info["description"],
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
        "tomli>=2.0",
        "urllib3>=1.26",
        "requests-aws4auth>=1.1",
        "deepdiff>=6.2",
    ],
    python_requires=">=3.9",
    include_package_data=True,
)
