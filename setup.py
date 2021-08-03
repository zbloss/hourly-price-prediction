from setuptools import find_packages, setup
from os import path

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

with open(path.join(this_directory, 'LICENSE'), encoding='utf-8') as f:
    license_ = f.read()

setup(
    name="hourly_price_prediction",
    packages=find_packages(),
    version="0.1.0",
    description="Naive Algo-Trading application that uses a Data Science Model for predicting the hourly close price of an asset and then buying or selling that asset based on the prediction.",
    author="Zachary Bloss",
    license=license_,
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=[
        "pandas>=1.3.1",
        "scikit-learn>=0.24.2",
        "cbpro>=1.1.4",
        "boto3>=1.18.12"
    ]
)
