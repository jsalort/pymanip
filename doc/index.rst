.. pymanip documentation master file, created by
   sphinx-quickstart on Mon Nov 25 12:25:20 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to pymanip's documentation!
===================================

pymanip is the main package that we use for data acquisition and monitoring of
our experimental systems in the Convection group at 
`Laboratoire de physique de l'ENS de Lyon <http://www.ens-lyon.fr/PHYSIQUE>`_.
It can be seen as an extension
of the :mod:`fluidlab` module, which it heavily uses.
It is available freely under the French 
`CECILL-B license <https://cecill.info/licences/Licence_CeCILL-B_V1-en.html>`_
in the hope that it can be useful to others. But it is provided AS IS, without any warranty as to
its commercial value, its secured, safe, innovative or relevant nature.

Unlike FluidLab_, pymanip does not garantee any long term stability, and may change the API
in the future without warning.
However, some parts of the pymanip module may eventually be integrated into 
FluidLab_, once they are stable enough.

The pymanip module is a set of tools for data acquisition and data management. Its goals are the
following:

- management of experimental “sessions”, for storing and retriving data, and useful live tools for experimental monitoring over long times, such as live plot, automated emails, and remote access of the live data, and also simple interrupt signal management;
- simplify access to FluidLab_ instrument classes;
- experimental implementation of asynchroneous video acquisition and DAQ acquisition;
- experimental extension of FluidLab_ interface and instrument classes with asynchroneous methods;
- miscellaneous CLI tools for saved session introspection, live video preview, live oscilloscope and spectrum analyser-style DAQ preview, and VISA/GPIB scanning.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   sessions/asyncsession
   instruments/instruments
   video/introduction
   acquisition/index
   cli/intro
   miscellaneous

.. _FluidLab: https://foss.heptapod.net/fluiddyn/fluidlab 

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
