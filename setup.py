#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import re

from setuptools import find_packages, setup

with io.open("osman/__init__.py", encoding="utf_8_sig") as version_file:
    __version__ = re.search(
        r"""__version__\s*=\s*[\'"]([^\'"]*)[\'"]""", version_file.read()
    ).group(1)

with open("README.md", mode="r", encoding="utf-8") as readme_file:
    long_description = readme_file.read()

setup(
    name="osman",
    version=__version__,
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
        "opensearch-py>=2.0.0",
        "parameterized>=0.8.1",
        "pytest>=7.1.3",
    ],
    python_requires=">=3.8",
    include_package_data=True,
)
