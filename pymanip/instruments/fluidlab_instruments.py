#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""

This module contains all the instrument classes available in fluidlab.

List of supported instruments:

"""

from __future__ import print_function
import sys
import fluidlab.instruments as instruments
import pymanip

if hasattr(pymanip, "pymanip_import_verbose"):
    verbose_import = pymanip.pymanip_import_verbose
else:
    verbose_import = False

__all__ = []

if verbose_import:
    print("Supported instruments:")

for instrument_type in instruments.__all__:
    exec("import fluidlab.instruments." + instrument_type + " as " + instrument_type)
    exec("instrument_type_module = " + instrument_type)
    __doc__ += "* " + instrument_type + ": "
    if verbose_import:
        sys.stdout.write("* " + instrument_type + ": ")
    for instrument_file in instrument_type_module.__all__:  # noqa: F821
        try:
            exec(
                "import fluidlab.instruments."
                + instrument_type
                + "."
                + instrument_file
                + " as "
                + instrument_file
            )
            exec("instrument_file_module = " + instrument_file)
            for instrument_classname in instrument_file_module.__all__:  # noqa: F821
                exec(
                    "from fluidlab.instruments."
                    + instrument_type
                    + "."
                    + instrument_file
                    + " import "
                    + instrument_classname
                )
                __doc__ += instrument_classname + " "
                if verbose_import:
                    sys.stdout.write(instrument_classname + " ")
                __all__.append(instrument_classname)
        except ImportError:
            print(
                "Unable to import",
                instrument_type + "." + instrument_file + "." + instrument_classname,
            )

    __doc__ += "\n"
    if verbose_import:
        sys.stdout.write("\n")

__doc__ += """
Example of usage:

from pymanip.instruments import Agilent34401a
from pymanip.interfaces import GPIBInterface

multiplexer = Agilent34401a(GPIBInterface(0,5))
"""
