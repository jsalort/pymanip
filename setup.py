#! /usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='pymanip',
      version='0.1',
      description='Python framework for experiments',
      long_description=readme(),
      url='http://www.juliensalort.org/git/?p=pymanip.git',
      author='Julien Salort',
      author_email='julien.salort@ens-lyon.fr',
      license='Apache',
      packages=['pymanip'],
      install_requires=[
        'h5py',
      ],
      include_package_data=True,
      zip_safe=False)
