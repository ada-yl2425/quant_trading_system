from setuptools import setup, find_packages

setup(
    name="quant_trading_system",
    version="1.0.0",
    description="Online Learning Tree Model for Quantitative Trading",
    author="ada-yl2425",
    packages=find_packages(),
    install_requires=[
        "pandas>=1.5.0",
        "numpy>=1.21.0", 
        "scikit-learn>=1.0.0",
        "xgboost>=1.5.0",
        "yfinance>=0.2.0",
        "matplotlib>=3.5.0",
        "seaborn>=0.11.0",
        "scipy>=1.7.0",
    ],
    python_requires=">=3.8",
)