#! /usr/bin/env python
# -*- coding: utf-8 -*-

#from distutils.core import setup
from setuptools import setup


def readme():
    with open('README.md') as f:
        return f.read()


setup(name='pymanip',
      version='0.3b0',
      description='Python framework for experiments',
      long_description=readme(),
      url='https://github.com/jsalort/pymanip',
      author='Julien Salort',
      author_email='julien.salort@ens-lyon.fr',
      license='CeCILL-B',
      packages=['pymanip'],
      install_requires=['h5py', 'clint', 'fluidlab (>=0.0.3)',
                        'opencv-python', 'progressbar2',
                        'aiohttp', 'aiohttp_jinja2'])
