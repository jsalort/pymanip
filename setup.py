#! /usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(name='pymanip',
      version='0.1',
      description='Python framework for experiments',
      url='http://www.juliensalort.org/git/?p=pymanip.git',
      author='Julien Salort',
      author_email='julien.salort@ens-lyon.fr',
      license='Apache',
      packages=['pymanip'],
      install_requires=[
        'h5py',
      ],
      zip_safe=False)