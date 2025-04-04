#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="rebang",
    version="1.0.0",
    author="AnonBot",
    description="热榜 Today 网站爬虫工具",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/rebang",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "selenium>=4.0.0",
        "beautifulsoup4>=4.9.0",
        "requests>=2.25.0",
    ],
    entry_points={
        "console_scripts": [
            "rebang=rebang.cli:main",
        ],
    },
)
