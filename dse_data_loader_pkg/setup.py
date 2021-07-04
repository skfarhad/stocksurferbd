import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="dse-data-loader",
    version="0.0.2",
    author="Sk Farhad",
    author_email="sk.farhad.eee@gmail.com",
    description="This is a tool to download stock market data of Dhaka Stock Exchange.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/skfarhad/algo-trading/tree/master/dse_data_loader_pkg",
    project_urls={
        "Bug Tracker": "https://github.com/skfarhad/algo-trading/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'requests',
        'pandas',
        'beautifulsoup4'
    ],
    # package_dir={"": "src"},
    # packages=setuptools.find_packages(where="dse_data_loader"),
    packages=['dse_data_loader'],
    python_requires=">=3.6",
    zip_safe=False
)
