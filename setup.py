#! /usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

def readme():
    with open('README.md') as f:
        return f.read()

setup(name='pymanip',
      version='0.1',
      description='Python framework for experiments',
      long_description=readme(),
      url='https://github.com/jsalort/pymanip',
      author='Julien Salort',
      author_email='julien.salort@ens-lyon.fr',
      license='CeCILL-B',
      packages=['pymanip'],
      install_requires=[
        'h5py', #'clint', 'fluidlab', 'fluiddyn',
      ],
      include_package_data=True,
      zip_safe=False)
