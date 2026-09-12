from setuptools import setup, find_packages

setup(
    name="apcv",
    version="0.1.0",
    description="Agent Policy Conformance Validator - Verify AI Agents comply with declared policies",
    author="APCV Team",
    license="Apache 2.0",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "langgraph>=0.1.0",
        "pydantic>=2.0",
        "pyyaml>=6.0",
        "jsonschema>=4.0",
        "typer>=0.9",
        "wrapt>=1.14",
        "docker>=6.0",
        "fastapi>=0.100",
        "uvicorn>=0.23",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "pytest-mock>=3.10",
            "black>=23.0",
            "mypy>=1.0",
            "pylint>=2.17",
        ],
        "test": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "pytest-mock>=3.10",
        ],
    },
    entry_points={
        "console_scripts": [
            "apcv=apcv.cli.main:app",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
