from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="flowguard",
    version="0.1.0",
    author="Nathan D'Souza",
    description="Deterministic workflow enforcement for AI agents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nathandsouza/flowguard",
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
    install_requires=[
        "pyyaml>=6.0",
        "click>=8.0",
        "rich>=13.0",
        "pydantic>=2.0",
    ],
    entry_points={
        "console_scripts": [
            "flowguard=flowguard.cli:main",
        ],
    },
)