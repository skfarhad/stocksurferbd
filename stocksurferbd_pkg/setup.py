import setuptools

with open("../README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="stocksurferbd",
    version="0.1.3",
    author="Sk Farhad",
    author_email="sk.farhad.eee@gmail.com",
    description="A Python library for downloading stock market data of Dhaka Stock"
                " Exchange(DSE) and Chittagong Stock Exchange(CSE).",
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
        'requests==2.32.3',
        'pandas==2.2.2',
        'openpyxl==3.1.5',
        'beautifulsoup4==4.9.3',
        'matplotlib==3.9.2',
        'mplfinance==0.12.10b0',
        'pyti==0.2.2',
        'tapy==1.9.1',
    ],
    packages=['stocksurferbd'],
    python_requires=">=3.10",
    zip_safe=False
)


# python setup.py sdist bdist_wheel
# twine upload dist/*
