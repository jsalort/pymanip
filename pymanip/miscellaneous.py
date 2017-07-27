#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""

This module contains miscellaneous functions:

 - scanGpib

"""

from __future__ import print_function, unicode_literals

import platform
import warnings

if platform.system() == 'Linux':
    try:
        import gpib
        has_gpib = True
    except:
        print('Warning: Linux-GPIB Python bindings not found')
        has_gpib = False
        pass
else:
    has_gpib = False

def scanGpib(board):
    if not has_gpib:
        warnings.warn('Linux-GPIB is not available. ScanGpib with VISA not implemented at the moment.', RuntimeWarning, stacklevel=2)
    else:
        for pad in range(1,31):
            listen = gpib.listener(board, pad)
            #print(board, pad, listen)
            if listen:
                print('GPIB' + str(board) + '::' + str(pad))
                try:
                    ud = gpib.dev(board, pad, 0, 10, 1, 0)
                    if (ud > 0):
                        gpib.write(ud, "*CLS;*IDN?")
                        description = gpib.read(ud, 256)
                        print(description.strip().decode('ascii'))
                except:
                    pass
