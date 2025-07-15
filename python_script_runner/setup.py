from setuptools import setup, find_packages

setup(
    name="python_script_runner_tools",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "openpyxl",
        "lxml",
    ],
    author="Kubiya",
    description="Python Script Runner tools for Kubiya",
    python_requires=">=3.8",
) 