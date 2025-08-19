#!/usr/bin/env python3
"""
Setup script for Miki Miki - AI-Powered Browser Automation
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="miki-miki",
    version="1.0.0",
    author="Flash Dynamics Syndicate",
    author_email="info@fdsyd.com",
    description="AI-powered browser automation tool using Google's Gemini Vision AI",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/29ayx/miki-miki",
    project_urls={
        "Bug Tracker": "https://github.com/29ayx/miki-miki/issues",
        "Documentation": "https://github.com/29ayx/miki-miki#readme",
        "Source Code": "https://github.com/29ayx/miki-miki",
        "Website": "https://fdsyd.com",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Internet :: WWW/HTTP :: Browsers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
        ],
        "docs": [
            "sphinx>=4.0",
            "sphinx-rtd-theme>=1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "miki-miki=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.json", "*.png", "*.md"],
    },
    keywords=[
        "ai",
        "automation",
        "browser",
        "gemini",
        "selenium",
        "web-scraping",
        "artificial-intelligence",
        "machine-learning",
        "vision",
        "google-ai",
    ],
    platforms=["Windows", "Linux", "macOS"],
    license="MIT",
    zip_safe=False,
)
