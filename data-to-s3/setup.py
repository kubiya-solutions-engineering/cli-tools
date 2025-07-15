from setuptools import setup, find_packages

setup(
    name="data_to_s3_tools",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "kubiya-sdk>=0.1.0",
        "requests>=2.31.0",
        "pyyaml>=6.0.1",
        "pandas>=1.5.0",
        "boto3>=1.26.0",
    ],
    author="Kubiya",
    description="Data processing and S3 upload tools for Kubiya",
    python_requires=">=3.8",
) 