[![Build Status](https://travis-ci.com/jsalort/pymanip.svg?branch=master)](https://travis-ci.com/jsalort/pymanip)
[![PyPI version](https://badge.fury.io/py/pymanip.svg)](https://badge.fury.io/py/pymanip)
[![Documentation Status](https://readthedocs.org/projects/pymanip/badge/?version=latest)](https://pymanip.readthedocs.io/en/latest/?badge=latest)

pymanip
=======

Description and goals
---------------------

pymanip is the main package that we use for data acquisition and monitoring of
our experimental systems in the Convection group at 
[Laboratoire de physique de l'ENS de Lyon](http://www.ens-lyon.fr/PHYSIQUE).
It can be seen as an extension
of the [FluidLab](https://foss.heptapod.net/fluiddyn/fluidlab) module, which it heavily uses.
It is available freely under the French 
[CECILL-B license](https://cecill.info/licences/Licence_CeCILL-B_V1-en.html)
in the hope that it can be useful to others. But it is provided AS IS, without any warranty as to
its commercial value, its secured, safe, innovative or relevant nature.

Unlike FluidLab, pymanip does not garantee any long term stability, and may change the API
in the future without warning.
However, some parts of the pymanip module may eventually be integrated into 
FluidLab, once they are stable enough.

The pymanip module is a set of tools for data acquisition and data management. Its goals are the
following:

- management of experimental “sessions”, for storing and retriving data, and useful live tools for experimental monitoring over long times, such as live plot, automated emails, and remote access of the live data, and also simple interrupt signal management;
- simplify access to FluidLab instrument classes;
- experimental implementation of asynchroneous video acquisition and DAQ acquisition;
- experimental extension of FluidLab interface and instrument classes with asynchroneous methods;
- miscellaneous CLI tools for saved session introspection, live video preview, live oscilloscope and spectrum analyser-style DAQ preview, and VISA/GPIB scanning.

Documentation
-------------

The documentation is available at [readthedocs](https://pymanip.readthedocs.io/en/latest/).

Installation
------------

The package can be installed from [pypi](https://pypi.org/project/pymanip/) using `pip`:

```
python -m pip install pymanip
```

or can be installed from github

```
git clone https://github.com/jsalort/pymanip.git
cd pymanip
python -m pip install -e .
```

