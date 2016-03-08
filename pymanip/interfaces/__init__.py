#! /usr/bin/env python
# -*- coding: utf-8 -*-

import platform

if platform.system() == 'Linux':
  try:
    from fluidlab.instruments.interfaces.linuxgpib import GPIBInterface
  except:
    print 'Warning: Linux-GPIB Python bindings not found'
    pass
  
try:
  from fluidlab.instruments.interfaces.visa import PyvisaInterface
except:
  print 'Warning: PyVISA not found'
  pass
  
try:
  from fluidlab.instruments.interfaces.serial_inter import SerialInterface
except:
  print 'Warning: SerialInterface not found'
  pass