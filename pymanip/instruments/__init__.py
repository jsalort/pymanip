#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import fluidlab.instruments as instruments
verbose_import = False
__all__ = []

if verbose_import:
    print 'Supported instruments:'

for instrument_type in instruments.__all__:
    exec("import fluidlab.instruments." + instrument_type + " as " + instrument_type)
    exec("instrument_type_module = " + instrument_type)
    if verbose_import:
        sys.stdout.write('* ' + instrument_type + ': ')
    for instrument_file in instrument_type_module.__all__:
        exec("import fluidlab.instruments." + instrument_type + "." + instrument_file + " as " + instrument_file)
        exec("instrument_file_module = " + instrument_file)
        for instrument_classname in instrument_file_module.__all__:
            exec("from fluidlab.instruments." + instrument_type + "." + instrument_file + " import " + instrument_classname)
            if verbose_import:
                sys.stdout.write(instrument_classname + " ")
            __all__.append(instrument_classname)
    if verbose_import:
        sys.stdout.write("\n")
