#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys
import h5py
import numpy as np
import time
import inspect
import matplotlib.pyplot as plt
import warnings
import smtplib, base64, quopri
import tempfile
from platform import platform
from clint.textui import colored

def boldface(string):
  return "\x1b[1;1m" + string + "\x1b[0;0m"
  
class Session:
  def __init__(self, session_name, variable_list=[]):
    self.session_name = session_name
    self.storename = session_name + '.hdf5'
    self.datname = session_name + '.dat'
    self.logname = session_name + '.log'
    self.datfile = open(self.datname, 'a')
    self.logfile = open(self.logname, 'a')
    self.session_opening_time = time.time()
    if platform().startswith('Windows'):
        self.dateformat = '%A %d %B %Y - %X (%z)'
    else:
        self.dateformat = '%A %e %B %Y - %H:%M:%S (UTC%z)'
    date_string = time.strftime(self.dateformat, time.localtime(self.session_opening_time))
    self.logfile.write("Session opened on " + date_string)
    self.logfile.flush()
    try:
      self.store = h5py.File(self.storename, 'r+')
      self.dset_time = self.store["time"]
      self.grp_variables = self.store["variables"]
      original_size = self.dset_time.len()
      arr = np.zeros( (original_size,) )
      new_headers = False
      if len(variable_list) != len(self.grp_variables.keys()):
        new_headers = True
      for var in variable_list:
        if var not in self.grp_variables.keys():
          self.grp_variables.create_dataset(var, chunks=True, maxshape=(None,), data=arr)
          new_headers = True
      print colored.blue(boldface("Session reloaded from file ") + self.storename)
      if original_size > 0:
        last_t = self.dset_time[original_size-1]
        date_string = time.strftime(self.dateformat, time.localtime(last_t))
        print boldface("Last point recorded:") + " " + date_string
    except IOError:
      self.store = h5py.File(self.storename, 'w')
      self.dset_time = self.store.create_dataset("time", chunks=True, maxshape=(None,), shape=(0,), dtype=float)
      self.grp_variables = self.store.create_group("variables")
      new_headers = True
      for var in variable_list:
        self.grp_variables.create_dataset(var, chunks=True, maxshape=(None,), shape=(0,), dtype=float)
    if new_headers:
      self.datfile.write('Time')
      for var in variable_list:
        self.datfile.write(' ' + var)
      self.datfile.write("\n")
    self.opened = True
    self.email_started = False
    self.email_lastSent = 0.0
    
  def disp(self, texte):
    print texte
    if self.email_started:
      self.email_body = self.email_body + texte + '<br />\n'
    if not texte.endswith("\n"):
      texte = texte + "\n"
    self.logfile.write(texte)
    self.logfile.flush()
      
  def log_addline(self):
    stack = inspect.stack()
    try:
      dict_caller = stack[1][0].f_locals
    finally:
      del stack
    newsize = self.dset_time.len()+1
    self.dset_time.resize( (newsize,) )
    self.dset_time[newsize-1] = time.time()
    self.datfile.write("%f" % self.dset_time[newsize-1])
    for varname in self.grp_variables.keys():
      d = self.grp_variables[varname]
      d.resize( (newsize,) )
      try:
        d[newsize-1] = dict_caller[varname]
        self.datfile.write(" %f" % dict_caller[varname])
      except:
        print colored.red('Variable is not defined: ') + varname
        d[newsize-1] = 0.
        pass
    self.datfile.write("\n")
    self.datfile.flush()
    self.store.flush()
  
  def log(self, varname):
    if varname == 'time' or varname == 't':
      return self.dset_time.value
    elif varname in self.grp_variables.keys():
      return self.grp_variables[varname].value
    else:
      print colored.red('Variable is not defined: ') + varname
    
  def log_plot(self, fignum, varlist, maxvalues=1000):
    plt.figure(fignum)
    plt.clf()
    plt.ion()
    plt.show()
    t = self.log('t')
    t = (t-t[0])/3600.
    if len(t) > maxvalues:
      debut = len(t) - 1000
      fin = len(t)
    else:
      debut = 0
      fin = len(t)
    for var in varlist:
      plt.plot(t[debut:fin], self.log(var)[debut:fin], 'o-', label=var)
    plt.xlabel('t [h]')
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

  def start_email(self, from_addr, to_addrs, host, subject=None, port=25):
    self.email_host = host
    self.email_port = port
    self.email_from_addr = from_addr
    self.email_to_addrs = to_addrs
    date_string = time.strftime(self.dateformat, time.localtime(time.time()))
    if subject != None:
      self.email_subject = subject
    else:
      self.email_subject = self.session_name
    self.email_body = "<html><body>\n<strong>**************************************************</strong><br />\n<strong>" + date_string + "</strong><br />\n" + self.session_name + "<br />\n<strong>**************************************************</strong><br /><br />\n\n"
    self.email_figlist = []
    self.email_started = True
    
  def add_figure_to_email(self, figNum):
    self.email_figlist.append(figNum)
    
  def stop_email(self):
    success = False
    smtp = smtplib.SMTP(self.email_host, self.email_port)
    self.email_body = self.email_body + "</body></html>"
    
    useMime = False
    if len(self.email_figlist) > 0:
      useMime = True
      
    mime_boundary = 'pymanip-MIME-delimiter'
    if useMime:
      email_header = 'Content-type: multipart/mixed; boundary="' + mime_boundary + '"\n'
      email_header = email_header + 'MIME-version: 1.0\n'
    else:
      email_header = 'Content-Type: text/html\n'
      email_header = email_header + 'Content-Transfer-Encoding: quoted-printable\n'
    email_header = email_header + 'User-Agent: pymanip\n'
    email_header = email_header + 'To: '
    if len(self.email_to_addrs) == 1:
      email_header = email_header + self.email_to_addrs[0] + '\n'
    else:
      for addr in self.email_to_addrs[:-1]:
        email_header = email_header + addr + ', '
      email_header = email_header + self.email_to_addrs[-1] + '\n'
    email_header = email_header + 'Subject: ' + self.email_subject
    
    if useMime:
      body = "This is a multi-part message in MIME format.\n"
      # Add text/html MIME part
      body = body + '--' + mime_boundary + '\n'
      body = body + 'Content-Type: text/html; charset=UTF-8\n'
      body = body + 'Content-Transfer-Encoding: quoted-printable\n\n'
      body = body + quopri.encodestring(self.email_body) + '\n'
      
      # Add figures
      for fig in self.email_figlist:
        plt.figure(fig)
        (fd, fname) = tempfile.mkstemp(suffix='.png')
        f_png = os.fdopen(fd, 'wb')
        plt.savefig(f_png)
        f_png.close()
        with open(fname, 'rb') as image_file:
          encoded_figure = base64.b64encode(image_file.read())
        os.remove(fname)
        # Add image/png MIME part
        body = body + '--' + mime_boundary + '\n'
        body = body + 'Content-Type: image/png\n'
        body = body + 'Content-Disposition: inline\n'
        body = body + 'Content-Transfer-Encoding: base64\n\n'
        for i in range(0,len(encoded_figure),76):
          debut = i
          fin = i + 75
          if fin >= len(encoded_figure):
            fin = len(encoded_figure)-1
          body = body + encoded_figure[debut:(fin+1)] + '\n'
          
      # Send email
      try:
        error_list = smtp.sendmail(
          self.email_from_addr, 
          self.email_to_addrs, 
          email_header + '\n' + body + '\n' + '--' + mime_boundary + '--\n')
        if len(error_list) == 0:
          success = True
      except smtplib.SMTPHeloError:
        print 'SMTP Helo Error'
        pass
      except smtplib.SMTPRecipientsRefused:
        print 'Some recipients have been rejected by SMTP server'
        pass
      except smtplib.SMTPSenderRefused:
        print 'SMTP server refused sender ' + self.email_from_addr
        pass
      except smtplib.SMTPDataError:
        print 'SMTP Data Error'
        pass
        
    else:
      try:
        error_list = smtp.sendmail(
          self.email_from_addr, 
          self.email_to_addrs, 
          email_header + '\n' + quopri.encodestring(self.email_body))
        if len(error_list) == 0:
          success = True
      except smtplib.SMTPHeloError:
        print 'SMTP Helo Error'
        pass
      except smtplib.SMTPRecipientsRefused:
        print 'Some recipients have been rejected by SMTP server'
        pass
      except smtplib.SMTPSenderRefused:
        print 'SMTP server refused sender ' + self.email_from_addr
        pass
      except smtplib.SMTPDataError:
        print 'SMTP Data Error'
        pass
        
    smtp.quit()
    self.email_body = ''
    self.email_started = False
    self.email_figlist = []
    if success:
      self.email_lastSent = time.time()
      date_string = time.strftime(self.dateformat, time.localtime(self.email_lastSent))
      print date_string + ': Email successfully sent.'

  def time_since_last_email(self):
    return time.time() - self.email_lastSent
    
  def Stop(self):
    if self.email_started:
      self.stop_email()
    if self.opened:
      self.store.close()
      self.datfile.close()
      date_string = time.strftime(self.dateformat, time.localtime(time.time()))
      self.logfile.write("Session closed on " + date_string)
      self.logfile.flush()
      self.logfile.close()
      self.opened = False
      
  def __del__(self):
    self.Stop()
