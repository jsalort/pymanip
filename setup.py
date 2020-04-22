#! /usr/bin/env python
# -*- coding: utf-8 -*-

# from distutils.core import setup
from setuptools import setup, find_packages


def readme():
    with open("README.md", encoding="utf8") as f:
        return f.read()


setup(
    name="pymanip",
    version="0.3.3",
    description="Python framework for experiments",
    long_description=readme(),
    long_description_content_type="text/markdown",
    url="https://pypi.org/project/pymanip/",
    project_urls={
        "Documentation": "https://pymanip.readthedocs.io/en/latest/",
        "Source Code": "https://github.com/jsalort/pymanip",
    },
    author="Julien Salort",
    author_email="julien.salort@ens-lyon.fr",
    license="CeCILL-B",
    packages=find_packages(),
    install_requires=[
        "h5py",
        "fluiddyn >= 0.3.2",
        "fluidlab >=0.1.0",
        "progressbar2",
        "aiohttp",
        "aiohttp_jinja2",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
