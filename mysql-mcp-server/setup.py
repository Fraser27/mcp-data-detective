"""
Setup script for MySQL MCP Server
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mysql-mcp-server-strands",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="MySQL MCP Server using Strands Agents SDK",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/mysql-mcp-server-strands",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "strands-agents>=0.1.0",
        "strands-agents-tools>=0.1.0",
        "mysql-connector-python>=8.0.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "mysql-mcp-server=mysql_mcp_server.server:main",
        ],
    },
)
