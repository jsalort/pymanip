#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys
import h5py
import numpy as np
import time
import inspect
import matplotlib.pyplot as plt
import warnings

def colorname_to_colorcode(color):
  if color == "red" or color == "Red" or color == "r":
    colorcode = 31
  elif color == "green" or color == "Green" or color == "g":
    colorcode = 32
  elif color == "yellow" or color == "Yellow" or color == "y":
    colorcode = 33
  elif color == "blue" or color == "Blue" or color == "b":
    colorcode = 34
  elif color == "purple" or color == "Purple" or color == "p":
    colorcode = 35
  elif color == "cyan" or color == "Cyan" or color == "c":
    colorcode = 36
  elif color == "black" or color == "Black" or color == "k":
    colorcode = 30
  elif color == "white" or color == "White" or color == "w":
    colorcode = 37
  else:
    print 'Warning: unknown color', color
    colorcode = 30
  return str(colorcode)

def typefacename_to_typefacecode(typeface):
  if typeface == "regular" or typeface == "Regular":
    typefacecode = 0
  elif typeface == "bold" or typeface == "Bold":
    typefacecode = 1
  elif typeface == "underline" or typeface == "Underline" or typeface == "underlined" or typeface == "_":
    typefacecode = 4
  else:
    print 'Warning: unknown typeface', typeface
    typefacecode = 0
  return str(typefacecode)

def boldface(string):
  return "\x1b[1;1m" + string + "\x1b[0;0m"

def print_formatted(string, color="black", typeface="regular"):
  if color != "black" or typeface != "regular":
    formatted_string = "\x1b[" + colorname_to_colorcode(color) + ";" + typefacename_to_typefacecode(typeface) + 'm' + string + "\x1b[0;0m\n"
    #formatted_string = "[" + colorname_to_colorcode(color) + ";" + typefacename_to_typefacecode(typeface) + 'm' + string + "[0;0m\n"
  else:
    formatted_string = string + "\n"
  sys.stdout.write(formatted_string)
  sys.stdout.flush()
  
class Session:
  def __init__(self, session_name, variable_list=[]):
    self.session_name = session_name
    self.storename = session_name + '.hdf5'
    self.datname = session_name + '.dat'
    try:
      self.store = h5py.File(self.storename, 'r+')
      self.dset_time = self.store["time"]
      self.grp_variables = self.store["variables"]
      original_size = self.dset_time.len()
      arr = np.zeros( (original_size,) )
      for var in variable_list:
        if var not in self.grp_variables.keys():
          self.grp_variables.create_dataset(var, chunks=True, maxshape=(None,), data=arr)
      print_formatted("Session reloaded from file " + self.storename, color="blue", typeface="bold")
      if original_size > 0:
        last_t = self.dset_time[original_size-1]
        date_string = time.strftime('%A %e %B %Y - %H:%M:%S (UTC%z)', time.localtime(last_t))
        print boldface("Last point recorded:") + " " + date_string
    except IOError:
      self.store = h5py.File(self.storename, 'w')
      self.dset_time = self.store.create_dataset("time", chunks=True, maxshape=(None,), shape=(0,), dtype=float)
      self.grp_variables = self.store.create_group("variables")
      for var in variable_list:
        self.grp_variables.create_dataset(var, chunks=True, maxshape=(None,), shape=(0,), dtype=float)
    self.opened = True
    
  def log_addline(self):
    stack = inspect.stack()
    try:
      dict_caller = stack[1][0].f_locals
    finally:
      del stack
    newsize = self.dset_time.len()+1
    self.dset_time.resize( (newsize,) )
    self.dset_time[newsize-1] = time.time()
    for varname in self.grp_variables.keys():
      d = self.grp_variables[varname]
      d.resize( (newsize,) )
      try:
        d[newsize-1] = dict_caller[varname]
      except:
        print_formatted('Variable is not defined: ' + varname, color="red", typeface="bold")
        d[newsize-1] = 0.
        pass
    self.store.flush()
  
  def log(self, varname):
    if varname == 'time' or varname == 't':
      return self.dset_time.value
    elif varname in self.grp_variables.keys():
      return self.grp_variables[varname].value
    else:
      print_formatted('Variable is not defined: ' + varname, color="red", typeface="bold")
    
      
  def log_plot(self, fignum, varlist):
    plt.figure(fignum)
    plt.clf()
    plt.ion()
    plt.show()
    t = self.log('t')
    t = (t-t[0])/3600.
    for var in varlist:
      plt.plot(t, self.log(var), 'o-', label=var)
    plt.legend(loc='upper left')
    plt.draw()
    with warnings.catch_warnings():
      warnings.simplefilter("ignore")
      plt.pause(0.0001)
    
  def sleep(self, duration):
    debut = time.time()
    while (time.time() - debut) < duration:
      sys.stdout.write("Sleeping for " + str(-int(time.time()-debut-duration)) + " s           \r")
      sys.stdout.flush()
      #time.sleep(1.0)
      with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        plt.pause(1.0)
    sys.stdout.write("\n")

      
  def Stop(self):
    if self.opened:
      self.store.close()
      #print "Press Enter to continue ..." 
      #raw_input()
      self.opened = False
      
  def __del__(self):
    self.Stop()
