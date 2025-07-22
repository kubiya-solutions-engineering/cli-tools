from setuptools import setup, find_packages

setup(
    name="argocd-cli-tools",
    version="1.0.0",
    description="High-performance ArgoCD CLI tools for Kubiya with intelligent caching",
    packages=find_packages(),
    install_requires=[
        "kubiya-sdk",
    ],
    python_requires=">=3.8",
)