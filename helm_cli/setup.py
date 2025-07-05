from setuptools import setup, find_packages

setup(
    name="helm_cli_tools",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "kubiya-sdk>=0.1.0",
        "pyyaml>=6.0.1",
    ],
    author="Kubiya",
    description="Helm CLI wrapper tools for Kubiya",
    python_requires=">=3.8",
) 