Shortcuts to FluidLab Instrument classes
========================================

The instrument classes are the basic objects that we use to communicate with various
scientific instruments. They are implemented in the FluidLab_ project in the :mod:`fluidlab.instruments` module.

The :mod:`pymanip.instruments` module, along with the :ref:`list_instruments cli command<list_instruments>` are simple tools, designed to simplify access to these classes.

Indeed, each instrument class in FluidLab_ is defined in separate sub-modules, which can result in long and convoluted `import` statements, such as

.. code-block:: python

    from fluidlab.instruments.chiller.lauda import Lauda
    from fluidlab.instruments.multiplexer.agilent_34970a import Agilent34970a
    from fluidlab.instruments.motor_controller.newport_xps_rl import NewportXpsRL

The :mod:`pymanip.instruments` module simplifies these import statements and allows to write

.. code-block:: python

    from pymanip.instruments import Lauda, Agilent34970a, NewportXpsRL

This is of course less efficient because this means that *all* instruments classes are actually loaded, but it makes the script easier to write and read.

The names of the available instrument classes can be conveniently obtained from the command line

.. code-block:: bash

    $ python -m pymanip list_instruments

.. _FluidLab: https://foss.heptapod.net/fluiddyn/fluidlab
