#! /usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup

def readme():
    with open('README.md') as f:
        return f.read()

setup(name='pymanip',
      version='0.2',
      description='Python framework for experiments',
      long_description=readme(),
      url='https://github.com/jsalort/pymanip',
      author='Julien Salort',
      author_email='julien.salort@ens-lyon.fr',
      license='CeCILL-B',
      packages=['pymanip'],
      requires=[
        'h5py', 'clint', 'fluidlab (>=0.0.3)', 'fluiddyn',
      ])
