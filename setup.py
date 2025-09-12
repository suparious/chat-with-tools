"""
Setup script for Chat with Tools Framework
"""

from setuptools import setup, find_packages
import os

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="chat-with-tools",
    version="0.1.0",
    author="Suparious",
    description="A modular framework for building AI agents with customizable tools",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Suparious/chat-with-tools",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "chat-with-tools=main:main",
            "chat-demo=demos.main:main",
            "council-chat=demos.council_chat:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.md", "*.txt"],
    },
)
