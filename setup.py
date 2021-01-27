import setuptools

from articleparser.version import __version__

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="articleparser",
    version=__version__,
    author="Sean Lo",
    author_email="seanlo96@hotmail.com",
    description="Extracts structured data from web articles.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sean-lo/articleparser",
    packages=setuptools.find_packages(),
    classifiers=[
        # As from http://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    install_requires=requirements,
    python_requires=">=3.8",
)