import setuptools

with open("../README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="stocksurferbd",
    version="0.0.12",
    author="Sk Farhad",
    author_email="sk.farhad.eee@gmail.com",
    description="This is a tool to download stock market data of Dhaka Stock Exchange.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/skfarhad/stocksurferbd",
    project_urls={
        "Bug Tracker": "https://github.com/skfarhad/stocksurferbd/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'requests==2.25.1',
        'pandas==1.2.3',
        'scipy==1.6.2',
        'beautifulsoup4==4.9.3',
        'matplotlib==3.4.1',
        'mplfinance==0.12.7a17',
        'pyti==0.2.2',
        'tapy==1.9.1',
    ],
    # package_dir={"": "src"},
    # packages=setuptools.find_packages(where="dse_data_loader"),
    packages=['stocksurferbd'],
    python_requires=">=3.6",
    zip_safe=False
)


# python setup.py sdist bdist_wheel
# twine upload dist/*
