#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import platform

if platform.system() == 'Linux':
    try:
        from fluidlab.instruments.interfaces.linuxgpib import GPIBInterface
    except ImportError:
        print('Warning: Linux-GPIB Python bindings not found')
        pass

try:
    from fluidlab.instruments.interfaces.visa import PyvisaInterface
except ImportError:
    print('Warning: PyVISA not found')
    pass

try:
    from fluidlab.instruments.interfaces.serial_inter import SerialInterface
except ImportError:
    print('Warning: SerialInterface not found')
    pass
