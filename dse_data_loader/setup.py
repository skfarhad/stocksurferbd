import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="dse-data-loader-sk-farhad",
    version="0.0.1",
    author="Sk Farhad",
    author_email="sk.farhad.eee@gmail.com",
    description="This is a tool to download stock price data of Dhaka Stock Exchange.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sk-farhad/dse-data-loader",
    project_urls={
        "Bug Tracker": "https://github.com/sk-farhad/dse-data-loader/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
)