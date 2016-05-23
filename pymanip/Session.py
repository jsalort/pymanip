#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module for experimental sessions.

Useful classes are Session and SavedSession.
"""

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
from datetime import datetime

acquisition_clock = None
acquisition_number = 0

__all__ = ['makeAcqName', 'SavedSession', 'Session']

def makeAcqName(comment=None):
    global acquisition_clock
    global acquisition_number

    if comment == "reset":
        acquisition_clock = None
        acquisition_number = 0
        name = None
    else:
        if acquisition_clock is None:
            acquisition_clock = datetime.now()
        acquisition_number = acquisition_number+1
        name = "%d-%02d-%02d_%02d-%02d-%02d" % (acquisition_clock.year,
                                                acquisition_clock.month,
                                                acquisition_clock.day,
                                                acquisition_clock.hour,
                                                acquisition_clock.minute,
                                                acquisition_clock.second)
        if comment is not None:
            name = name + "_" + comment
        name = name + "_" + str(acquisition_number)

    if name is not None:
        print "Acquisition name:", name
    return name

def boldface(string):
    return "\x1b[1;1m" + string + "\x1b[0;0m"

class BaseSession(object):
    def __init__(self, session_name):
        self.session_name = session_name
        self.storename = session_name + '.hdf5'
        if platform().startswith('Windows'):
            self.dateformat = '%A %d %B %Y - %X (%z)'
        else:
            self.dateformat = '%A %e %B %Y - %H:%M:%S (UTC%z)'
        self.session_opening_time = time.time()
        self.opened = False
        self.parameters_defined = False
        self.grp_datasets_defined = False
        self.allow_override_datasets = False

    def describe(self):
        # Logged variables
        if len(self.grp_variables.keys()) > 0:
            num_lines = self.dset_time.len()
            print 'List of saved variables: (%d lines)' % num_lines
            for var in self.grp_variables.keys():
                print ' ' + var
        # Datasets
        if self.grp_datasets_defined:
            print 'List of saved datasets:'
            for dataname in self.grp_datasets.keys():
                size = self.grp_datasets[dataname].size
                print ' ' + dataname + (' (%d points)' % size)
        # Parameters
        if self.parameters_defined:
            if len(self.parameters.keys()) > 0:
                print 'List of saved parameters:'
                for name in self.parameters.keys():
                    value = self.parameters[name]
                    #print type(value)
                    if isinstance(value, np.ndarray) and len(value) == 1:
                        value = value[0]
                    if name == 'email_lastSent':
                        print ' ' + name + ' = ' +  time.strftime(self.dateformat, time.localtime(value))
                    else:
                        print ' ' + name + ' = ' + str(value) + ' (' + str(type(value)) + ')'

    def has_dataset(self, name):
        if self.grp_datasets_defined:
            return (name in self.grp_datasets.keys())
        else:
            return False

    def dataset(self, name):
        if self.grp_datasets_defined:
            return self.grp_datasets[name].value

    def has_parameter(self, name):
        if self.parameters_defined:
            return (name in self.parameters.keys())
        else:
            return False

    def parameter(self, name):
        if self.parameters_defined:
            return self.parameters[name]

    def has_log(self, name):
        return (name in self.grp_variables.keys())

    def log_variable_list(self):
        return self.grp_variables.keys()
    
    def log(self, varname):
        if self.opened:
            if varname == 'Time' or varname == 'time' or varname == 't':
                return self.dset_time.value
            elif varname == '?':
                print 'List of saved variables:'
                for var in self.grp_variables.keys():
                    print var
            elif varname in self.grp_variables.keys():
                return self.grp_variables[varname].value
            else:
                print colored.red('Variable is not defined: ') + varname
        else:
            print colored.red('Session is not opened')

    def log_plot(self, fignum, varlist, maxvalues=1000):
        if self.opened:
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
            if isinstance(varlist, str):
                plt.plot(t[debut:fin], self.log(varlist)[debut:fin], 'o-', label=varlist)
            else:
                for var in varlist:
                    plt.plot(t[debut:fin], self.log(var)[debut:fin], 'o-', label=var)
            plt.xlabel('t [h]')
            plt.legend(loc='upper left')
            plt.draw()
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                plt.pause(0.0001)
        else:
            print colored.red('Session is not opened')

    def sleep(self, duration):
        debut = time.time()
        while (time.time() - debut) < duration:
            sys.stdout.write("Sleeping for " + str(-int(time.time()-debut-duration)) + " s                                   \r")
            sys.stdout.flush()
            #time.sleep(1.0)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                plt.pause(1.0)
        sys.stdout.write("\n")

class SavedSession(BaseSession):
    def __init__(self, session_name):
        super(SavedSession, self).__init__(session_name)
        self.store = h5py.File(self.storename, 'r')
        self.dset_time = self.store["time"]
        self.grp_variables = self.store["variables"]
        try:
            self.parameters = self.store.attrs
            self.parameters_defined = True
        except:
            self.parameters_defined = False
            pass
        try:
            self.grp_datasets = self.store["datasets"]
            self.grp_datasets_defined = True
        except:
            self.grp_datasets_defined = False
            pass
        self.opened = True
        print 'Loading saved session from file', self.storename
        total_size = self.dset_time.len()
        if total_size > 0:
            start_t = self.dset_time[0]
            end_t = self.dset_time[total_size-1]
            start_string = time.strftime(self.dateformat, time.localtime(start_t))
            end_string = time.strftime(self.dateformat, time.localtime(end_t))
            print colored.blue('*** Start date: ' + start_string)
            print colored.blue('***  End date: ' + end_string)
        elif not self.grp_datasets_defined:
            print colored.red('No logged variables')
        if self.grp_datasets_defined:
            timestamp_string = time.strftime(self.dateformat, time.localtime(self.grp_datasets.attrs['timestamp']))
            print colored.blue('*** Acquisition timestamp ' + timestamp_string)

    def __enter__(self):
        return self

    def __exit__(self, type, value, cb):
        self.exited = True
        
class Session(BaseSession):
    def __init__(self, session_name, variable_list=[], allow_override_datasets=False):
        super(Session, self).__init__(session_name)
        self.datname = session_name + '.dat'
        self.logname = session_name + '.log'
        self.datfile = open(self.datname, 'a')
        self.logfile = open(self.logname, 'a')
        self.allow_override_datasets = allow_override_datasets

        date_string = time.strftime(self.dateformat, time.localtime(self.session_opening_time))
        self.logfile.write("Session opened on " + date_string)
        self.logfile.flush()
        try:
            self.store = h5py.File(self.storename, 'r+')
            self.dset_time = self.store["time"]
            self.grp_variables = self.store["variables"]
            self.parameters = self.store.attrs
            self.parameters_defined = True
            try:
                self.grp_datasets = self.store["datasets"]
                self.grp_datasets_defined = True
            except:
                self.grp_datasets_defined = False
            pass
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
            self.parameters = self.store.attrs
            self.parameters_defined = True
            self.parameters['email_lastSent'] = 0.0
            new_headers = True
            for var in variable_list:
                self.grp_variables.create_dataset(var, chunks=True, maxshape=(None,), shape=(0,), dtype=float)
        if new_headers:
            self.datfile.write('Time')
            # attention: ne pas utiliser variable_list ici car
            # dans log_addline on utilise self.grp_variable.keys()
            # et l'ordre n'est pas le même
            for var in self.grp_variables.keys():
                self.datfile.write(' ' + var)
            self.datfile.write("\n")
        self.opened = True
        self.email_started = False

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

    def save_parameter(self, parameter_name, dict_caller=None):
        if dict_caller is None:
            stack = inspect.stack()
            try:
                dict_caller = stack[1][0].f_locals
            finally:
                del stack
        if isinstance(parameter_name, str):
            value = dict_caller[parameter_name]
            self.parameters[parameter_name] = value
        else:
            for var in parameter_name:
                value = dict_caller[var]
                self.parameters[var] = value

    def save_parameters(self, parameter_list):
        stack = inspect.stack()
        try:
            dict_caller = stack[1][0].f_locals
        finally:
            del stack
        self.save_parameter(parameter_list, dict_caller)

    def save_dataset(self, data_name, dict_caller=None):
        if dict_caller is None:
            stack = inspect.stack()
            try:
                dict_caller = stack[1][0].f_locals
            finally:
                del stack
        if not self.grp_datasets_defined:
            self.grp_datasets = self.store.create_group("datasets")
            self.grp_datasets_defined = True
        if data_name not in self.grp_datasets.keys():
            self.grp_datasets.attrs['timestamp'] = time.time()
            self.grp_datasets.create_dataset(data_name, chunks=True, maxshape=(None,), data=dict_caller[data_name])
        elif self.allow_override_datasets:
            new_length = len(dict_caller[data_name])
            if len(self.grp_datasets[data_name]) != new_length:
                self.grp_datasets[data_name].resize( (new_length,) )
            self.grp_datasets[data_name][:] = dict_caller[data_name]
            self.grp_datasets.attrs['timestamp'] = time.time()
            print colored.red('Warning: overriding existing dataset')
        else:
            raise NameError('Dataset is already defined. Use allow_override_datasets to allow override of existing saved datasets.')

    def save_datasets(self, data_list):
        stack = inspect.stack()
        try:
            dict_caller = stack[1][0].f_locals
        finally:
            del stack
        for data_name in data_list:
            self.save_dataset(data_name, dict_caller)

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
        if isinstance(self.email_to_addrs, str):
            email_header = email_header + self.email_to_addrs + '\n'
        elif isinstance(self.email_to_addrs, tuple):
            for addr in self.email_to_addrs[:-1]:
                email_header = email_header + addr + ', '
            email_header = email_header + self.email_to_addrs[-1] + '\n'
        else:
            raise ValueError('Adress list should be a string or a tuple')
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
            self.parameters['email_lastSent'] = time.time()
            date_string = time.strftime(self.dateformat, time.localtime(self.parameters['email_lastSent']))
            print date_string + ': Email successfully sent.'

    def time_since_last_email(self):
        try:
            last = self.parameters['email_lastSent']
        except:
            last = 0.0
            pass
        return time.time() - last

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
