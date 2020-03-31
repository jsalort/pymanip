#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module for experimental sessions.

Useful classes are Session and SavedSession.
"""

import os
import numpy as np
import time
import inspect
import matplotlib.pyplot as plt
import warnings

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=FutureWarning)
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    import h5py
import smtplib
import base64
import quopri
import tempfile

from datetime import datetime

from fluiddyn.util.terminal_colors import cprint

try:
    from convbox.myplot import ColorGenerator
except ImportError:
    import itertools

    def ColorGenerator():
        return itertools.cycle(["b", "r", "g", "k", "m", "c"])


import pymanip.mytime as mytime

try:
    from pathlib import Path

    has_pathlib = True
except ImportError:
    has_pathlib = False
from pymanip.mytime import dateformat

__all__ = ["makeAcqName", "SavedSession", "Session", "NameGenerator"]


def NameGenerator(prefix=None, postfix=None):
    acquisition_clock = datetime.now()
    acquisition_number = 1
    name = "%d-%02d-%02d_%02d-%02d-%02d" % (
        acquisition_clock.year,
        acquisition_clock.month,
        acquisition_clock.day,
        acquisition_clock.hour,
        acquisition_clock.minute,
        acquisition_clock.second,
    )
    if prefix:
        name = prefix + "_" + name
    if postfix:
        name = name + "_" + postfix
    while True:
        name_numbered = name + "_" + str(acquisition_number)
        print("Acquisition name:", name_numbered)
        yield name_numbered
        acquisition_number = acquisition_number + 1


defaultGenerator = None


def makeAcqName(comment=None):
    global defaultGenerator

    if (
        (defaultGenerator is None)
        or (comment == "reset")
        or (defaultGenerator.gi_frame.f_locals["postfix"] != comment)
    ):
        defaultGenerator = NameGenerator(postfix=comment)
    return next(defaultGenerator)


class BaseSession(object):
    def __init__(self, session_name=None):
        if session_name is None:
            session_name = makeAcqName()

        self.session_name = session_name
        self.storename = session_name + ".hdf5"
        self.session_opening_time = time.time()
        self.opened = False
        self.parameters_defined = False
        self.grp_datasets_defined = False
        self.allow_override_datasets = False

    def __str__(self):
        return self.session_name

    def describe(self):
        # Logged variables
        if len(self.grp_variables.keys()) > 0:
            num_lines = self.dset_time.len()
            print("List of saved variables: (%d lines)" % num_lines)
            for var in self.grp_variables.keys():
                print(" " + var)
        # Datasets
        if self.grp_datasets_defined:
            print("List of saved datasets:")
            for dataname in self.grp_datasets.keys():
                size = self.grp_datasets[dataname].size
                print(" " + dataname + (" (%d points)" % size))
        # Parameters
        if self.parameters_defined:
            if len(self.parameters.keys()) > 0:
                print("List of saved parameters:")
                for name in self.parameters.keys():
                    value = self.parameters[name]
                    # print(type(value))
                    if isinstance(value, np.ndarray) and len(value) == 1:
                        value = value[0]
                    if name == "email_lastSent":
                        theDateStr = time.strftime(dateformat, time.localtime(value))
                        print(" " + name + " = " + theDateStr)
                    else:
                        print(
                            " "
                            + name
                            + " = "
                            + str(value)
                            + " ("
                            + str(type(value))
                            + ")"
                        )

    def has_dataset(self, name):
        if self.grp_datasets_defined:
            return name in self.grp_datasets.keys()
        else:
            return False

    def dataset(self, name):
        if self.grp_datasets_defined:
            return self.grp_datasets[name][()]

    def dataset_names(self):
        if hasattr(self, "grp_datasets"):
            return self.grp_datasets.keys()
        return []

    def has_parameter(self, name):
        if self.parameters_defined:
            return name in self.parameters.keys()
        else:
            return False

    def parameter(self, name):
        if self.parameters_defined:
            return self.parameters[name]

    def has_log(self, name):
        if name == "Time" or name == "time" or name == "t":
            return True
        return name in self.grp_variables.keys()

    def log_variable_list(self):
        return self.grp_variables.keys()

    def log(self, varname):
        if self.opened:
            if varname == "Time" or varname == "time" or varname == "t":
                return self.dset_time[()]
            elif varname == "?":
                print("List of saved variables:")
                for var in self.grp_variables.keys():
                    print(var)
            elif varname in self.grp_variables.keys():
                return self.grp_variables[varname][()]
            else:
                cprint.red("Variable is not defined: " + varname)
        else:
            cprint.red("Session is not opened")

    def __getitem__(self, key):
        if self.has_log(key):
            return self.log(key)
        elif self.has_parameter(key):
            return self.parameter(key)
        elif self.has_dataset(key):
            return self.dataset(key)
        else:
            raise KeyError('Unknown key "' + key + '"')

    def log_plot(self, fignum, varlist, maxvalues=1000, plotfunc=plt.plot):
        if self.opened:
            plt.figure(fignum)
            plt.clf()
            plt.ion()
            plt.show()
            t = self.log("t")
            if len(t) > maxvalues:
                debut = len(t) - 1000
                fin = len(t)
            else:
                debut = 0
                fin = len(t)
            if t[debut] > self.session_opening_time:
                # tous les points sont nouveaux
                olddebut = None
                oldfin = None
                newdebut = debut
                newfin = fin
            elif t[-1] > self.session_opening_time:
                # certains points sont nouveaux
                bb = t > self.session_opening_time
                olddebut = debut
                oldfin = np.min(bb.argmax())
                newdebut = oldfin
                newfin = fin
            else:
                # les points sont tous anciens
                olddebut = debut
                oldfin = fin
                newdebut = None
                newfin = None
            if t[-1] - t[0] < 3600:
                t = (t - t[0]) / 60.0
                xlab = "t [min]"
            else:
                t = (t - t[0]) / 3600.0
                xlab = "t [h]"
            # print(olddebut, oldfin, newdebut, newfin)

            if isinstance(varlist, str):
                lab = varlist
                col = (0, 0, 1)
                if newdebut is not None:
                    plt.plot(
                        t[newdebut:newfin],
                        self.log(varlist)[newdebut:newfin],
                        "o-",
                        color=col,
                        mec=col,
                        mfc=col,
                        label=lab,
                    )
                    lab = None
                if olddebut is not None:
                    plt.plot(
                        t[olddebut:oldfin],
                        self.log(varlist)[olddebut:oldfin],
                        "o-",
                        mfc="none",
                        mec=col,
                        color=col,
                        label=lab,
                    )

            else:
                for var, coul in zip(varlist, ColorGenerator()):
                    lab = var
                    if newdebut is not None:
                        plotfunc(
                            t[newdebut:newfin],
                            self.log(var)[newdebut:newfin],
                            "o-",
                            mfc=coul,
                            mec=coul,
                            color=coul,
                            label=lab,
                        )
                        lab = None
                    if olddebut is not None:
                        plotfunc(
                            t[olddebut:oldfin],
                            self.log(var)[olddebut:oldfin],
                            "o-",
                            mfc="none",
                            mec=coul,
                            color=coul,
                            label=lab,
                        )

            plt.xlabel(xlab)
            plt.legend(loc="upper left")
            plt.draw()
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                plt.pause(0.0001)
        else:
            cprint.red("Session is not opened")

    def sleep(self, duration):
        mytime.sleep(duration)

    def __enter__(self):
        self.exited = False
        return self

    def __exit__(self, type_, value, cb):
        self.exited = True


class SavedSession(BaseSession):
    def __init__(
        self, session_name, cache_override=False, cache_location=".", verbose=True
    ):
        super(SavedSession, self).__init__(session_name)
        self.store = h5py.File(self.storename, "r")
        try:
            self.dset_time = self.store["time"]
        except KeyError:
            print("The file '" + self.storename + "' is not a pymanip session file.")
            raise RuntimeError("Wrong hdf5 data")
        self.grp_variables = self.store["variables"]
        self.verbose = verbose
        try:
            self.parameters = self.store.attrs
            self.parameters_defined = True
        except Exception:
            self.parameters_defined = False
            pass
        try:
            self.grp_datasets = self.store["datasets"]
            self.grp_datasets_defined = True
        except Exception:
            self.grp_datasets_defined = False
            pass
        self.opened = True
        if verbose:
            print("Loading saved session from file", self.storename)
        total_size = self.dset_time.len()
        if total_size > 0:
            start_t = self.dset_time[0]
            end_t = self.dset_time[total_size - 1]
            start_string = time.strftime(dateformat, time.localtime(start_t))
            end_string = time.strftime(dateformat, time.localtime(end_t))
            if verbose:
                cprint.blue("*** Start date: " + start_string)
                cprint.blue("***   End date: " + end_string)
        elif not self.grp_datasets_defined:
            if verbose:
                cprint.red("No logged variables")
        if self.grp_datasets_defined:
            timestamp_string = time.strftime(
                dateformat, time.localtime(self.grp_datasets.attrs["timestamp"])
            )
            if verbose:
                cprint.blue("*** Acquisition timestamp " + timestamp_string)
        self.cachestorename = os.path.join(
            os.path.realpath(cache_location), "cache", os.path.basename(self.storename)
        )
        if cache_override:
            self.cachemode = "w"
        else:
            self.cachemode = "r+"
        try:
            self.cachestore = h5py.File(self.cachestorename, self.cachemode)
            if verbose:
                cprint.yellow("*** Cache store found at " + self.cachestorename)
            self.has_cachestore = True
        except IOError:
            self.has_cachestore = False
            pass

    @property
    def cachedvars(self):
        if not hasattr(self, "has_cachestore"):
            return []
        if self.has_cachestore:
            return self.cachestore.keys()
        else:
            return []

    def cached(self, *args):
        """
        cached('var1', 'var2', ...)
        or
        cached(['var1', 'var2'])

        returns True if all specified variables are present in the cachestore
        """
        if len(args) == 1:
            name = args[0]
        else:
            name = [a for a in args]
        if isinstance(name, str):
            return name in self.cachedvars
        else:
            return all([(n in self.cachedvars) for n in name])

    def cachedvalue(self, varname):
        if self.has_cachestore:
            if self.verbose:
                cprint.yellow("Retrieving " + varname + " from cache")
            content = self.cachestore[varname]
            if hasattr(content, "value"):
                return content[()]
            else:
                result = list()
                i = 0
                while True:
                    try:
                        result.append(content[str(i)][()])
                        i = i + 1
                    except KeyError:
                        break
                return np.array(result)
        else:
            raise KeyError

    def cache(self, name, dict_caller=None):
        if dict_caller is None:
            stack = inspect.stack()
            try:
                dict_caller = stack[1][0].f_locals
            finally:
                del stack
        if not isinstance(name, str):
            for var in name:
                self.cache(var, dict_caller)
            return

        if not self.has_cachestore:
            try:
                os.mkdir(os.path.dirname(self.cachestorename))
            except OSError:
                pass
            try:
                self.cachestore = h5py.File(self.cachestorename, "w")
                self.has_cachestore = True
                cprint.yellow("*** Cache store created at " + self.cachestorename)
            except IOError as ioe:
                self.has_cachestore = False
                cprint.red("Cannot create cache store")
                cprint.red(ioe.message)

        if self.has_cachestore:
            cprint.yellow("Saving " + name + " in cache")

            if isinstance(dict_caller[name], list):
                # Sauvegarde d'une liste d'objets
                # Dans ce cas, on crée un groupe du nom "name" et on récurse
                # Si le groupe existe déjà, on le supprime et on le recrée
                try:
                    del self.cachestore[name]
                except KeyError:
                    pass
                grp = self.cachestore.create_group(name)
                for itemnum, item in enumerate(dict_caller[name]):
                    if not isinstance(item, (int, float)):
                        grp.create_dataset(
                            str(itemnum), chunks=True, data=item, compression="gzip"
                        )
                    else:
                        grp.create_dataset(str(itemnum), data=item)
            else:

                try:
                    new_length = len(dict_caller[name])
                except TypeError:
                    new_length = 1
                    pass
                if name in self.cachestore.keys():
                    if len(self.cachestore[name]) != new_length:
                        self.cachestore[name].resize((new_length,))
                    self.cachestore[name][:] = dict_caller[name]
                else:
                    if new_length > 1:
                        self.cachestore.create_dataset(
                            name, chunks=True, maxshape=(None,), data=dict_caller[name]
                        )
                    else:
                        self.cachestore.create_dataset(
                            name, chunks=True, maxshape=(None,), shape=(new_length,)
                        )
                        self.cachestore[name][:] = dict_caller[name]

    def __exit__(self, type, value, cb):
        """ Previous versions used __del__ which is bad
            practise because the gc triggering mechanism is
            an implementation detail of CPython.
            Therefore, one should either explicitly call
            Stop() or close(), or use a context manager
            (preferred way)
        """
        self.store.close()
        self.store = None
        self.opened = False
        if hasattr(self, "has_cachestore") and self.has_cachestore and self.cachestore:
            self.cachestore.close()
            self.has_cachestore = False
            self.cachestore = None
        super(SavedSession, self).__exit__(type, value, cb)


class Session(BaseSession):
    def __init__(self, session_name, variable_list=[], allow_override_datasets=False):
        if has_pathlib:
            if isinstance(session_name, Path):
                session_name = session_name.as_posix()
        super(Session, self).__init__(session_name)
        self.datname = session_name + ".dat"
        self.logname = session_name + ".log"
        self.datfile = open(self.datname, "a")
        self.logfile = open(self.logname, "a")
        self.allow_override_datasets = allow_override_datasets

        date_string = time.strftime(
            dateformat, time.localtime(self.session_opening_time)
        )
        self.logfile.write("Session opened on " + date_string)
        self.logfile.flush()
        try:
            self.store = h5py.File(self.storename, "r+")
            self.dset_time = self.store["time"]
            self.grp_variables = self.store["variables"]
            self.parameters = self.store.attrs
            self.parameters_defined = True
            try:
                self.grp_datasets = self.store["datasets"]
                self.grp_datasets_defined = True
            except Exception:
                self.grp_datasets_defined = False
            original_size = self.dset_time.len()
            arr = np.zeros((original_size,))
            new_headers = False
            if len(variable_list) != len(self.grp_variables.keys()):
                new_headers = True
            for var in variable_list:
                if var not in self.grp_variables.keys():
                    self.grp_variables.create_dataset(
                        var, chunks=True, maxshape=(None,), data=arr
                    )
                    new_headers = True
            cprint.blue("Session reloaded from file", bold=True, end=" ")
            cprint.blue(self.storename)
            if original_size > 0:
                last_t = self.dset_time[original_size - 1]
                date_string = time.strftime(dateformat, time.localtime(last_t))
                cprint.black("Last point recorded:", bold=True, end=" ")
                print(date_string)
        except IOError:
            self.store = h5py.File(self.storename, "w")
            self.dset_time = self.store.create_dataset(
                "time", chunks=True, maxshape=(None,), shape=(0,), dtype=float
            )
            self.grp_variables = self.store.create_group("variables")
            self.parameters = self.store.attrs
            self.parameters_defined = True
            self.parameters["email_lastSent"] = 0.0
            new_headers = True
            for var in variable_list:
                self.grp_variables.create_dataset(
                    var, chunks=True, maxshape=(None,), shape=(0,), dtype=float
                )
        if new_headers:
            self.datfile.write("Time")
            # attention: ne pas utiliser variable_list ici car
            # dans log_addline on utilise self.grp_variable.keys()
            # et l'ordre n'est pas le même
            for var in self.grp_variables.keys():
                self.datfile.write(" " + var)
            self.datfile.write("\n")
        self.opened = True
        self.email_started = False

    def disp(self, texte):
        print(texte)
        if self.email_started:
            self.email_body = self.email_body + texte + "<br />\n"
        if not texte.endswith("\n"):
            texte = texte + "\n"
        self.logfile.write(texte)
        self.logfile.flush()

    def log_addline(self, timestamp=None, dict_caller=None):
        if not dict_caller:
            stack = inspect.stack()
            try:
                dict_caller = stack[1][0].f_locals
            finally:
                del stack
        newsize = self.dset_time.len() + 1
        self.dset_time.resize((newsize,))
        if not timestamp:
            timestamp = time.time()
        self.dset_time[newsize - 1] = timestamp
        self.datfile.write("%f" % self.dset_time[newsize - 1])
        for varname in self.grp_variables.keys():
            d = self.grp_variables[varname]
            d.resize((newsize,))
            try:
                d[newsize - 1] = dict_caller[varname]
                self.datfile.write(" %f" % dict_caller[varname])
            except Exception:
                cprint.red("Variable is not defined: " + varname)
                d[newsize - 1] = 0.0
        self.datfile.write("\n")
        self.datfile.flush()
        self.store.flush()

    def save_remote_data(self, data):
        """
        Save data from RemoteObserver object as datasets and parameters
        """
        for k, v in data.items():
            # print(k,type(v),v)
            try:
                v[0]
                # we are iterable
                self.save_dataset(k, data)
            except (TypeError, KeyError):
                # we are not iterable
                if isinstance(v, dict):
                    # non reduced data, v is a dictionnary with two keys, 't' and 'value'
                    self.save_dataset(k, {k: v["value"]})
                    self.save_dataset(k + "_time", {k + "_time": v["t"]})
                else:
                    try:
                        # data must be a scalar
                        float(v)
                    except TypeError:
                        print("skipping", k, type(v))
                        continue
                    self.save_parameter(k, data)

    def save_parameter(self, parameter_name, dict_caller=None):
        if dict_caller is None:
            stack = inspect.stack()
            try:
                dict_caller = stack[1][0].f_locals
            finally:
                del stack
        if isinstance(parameter_name, str):
            try:
                value = dict_caller[parameter_name]
                self.parameters[parameter_name] = value
            except TypeError:
                print(f"Failed to save parameter {parameter_name:}")
                print(type(value))
                print(value)
                raise
        elif isinstance(parameter_name, dict):
            for k, v in parameter_name.items():
                self.parameters[k] = v
        else:
            for var in parameter_name:
                value = dict_caller[var]
                self.parameters[var] = value

    def save_parameters(self, parameter_list):
        """
        save_parameters( parameter_list )
        or
        save_parameters( parameter_dict)
        """

        if isinstance(parameter_list, dict):
            for k, v in parameter_list.items():
                self.parameters[k] = v
        else:
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
            self.grp_datasets.attrs["timestamp"] = time.time()
            self.grp_datasets.create_dataset(
                data_name, chunks=True, maxshape=(None,), data=dict_caller[data_name]
            )
        elif self.allow_override_datasets:
            new_length = len(dict_caller[data_name])
            if len(self.grp_datasets[data_name]) != new_length:
                self.grp_datasets[data_name].resize((new_length,))
            self.grp_datasets[data_name][:] = dict_caller[data_name]
            self.grp_datasets.attrs["timestamp"] = time.time()
            cprint.red("Warning: overriding existing dataset")
        else:
            raise NameError(
                "Dataset is already defined. Use allow_override_datasets to allow override of existing saved datasets."
            )

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
        date_string = time.strftime(dateformat, time.localtime(time.time()))
        if subject is not None:
            self.email_subject = subject
        else:
            self.email_subject = self.session_name
        self.email_body = (
            "<html><body>\n<strong>**************************************************</strong><br />\n<strong>"
            + date_string
            + "</strong><br />\n"
            + self.session_name
            + "<br />\n<strong>**************************************************</strong><br /><br />\n\n"
        )
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

        mime_boundary = "pymanip-MIME-delimiter"
        if useMime:
            email_header = (
                'Content-type: multipart/mixed; boundary="' + mime_boundary + '"\n'
            )
            email_header = email_header + "MIME-version: 1.0\n"
        else:
            email_header = "Content-Type: text/html\n"
            email_header = (
                email_header + "Content-Transfer-Encoding: quoted-printable\n"
            )
        email_header = email_header + "User-Agent: pymanip\n"
        email_header = email_header + "To: "
        if isinstance(self.email_to_addrs, str):
            email_header = email_header + self.email_to_addrs + "\n"
        elif isinstance(self.email_to_addrs, tuple):
            for addr in self.email_to_addrs[:-1]:
                email_header = email_header + addr + ", "
            email_header = email_header + self.email_to_addrs[-1] + "\n"
        else:
            raise ValueError("Adress list should be a string or a tuple")
        email_header = email_header + "Subject: " + self.email_subject

        if useMime:
            body = "This is a multi-part message in MIME format.\n"
            # Add text/html MIME part
            body = body + "--" + mime_boundary + "\n"
            body = body + "Content-Type: text/html; charset=UTF-8\n"
            body = body + "Content-Transfer-Encoding: quoted-printable\n\n"
            body = (
                body
                + quopri.encodestring(self.email_body.encode("utf-8")).decode("utf-8")
                + "\n"
            )

            # Add figures
            for fig in self.email_figlist:
                plt.figure(fig)
                (fd, fname) = tempfile.mkstemp(suffix=".png")
                f_png = os.fdopen(fd, "wb")
                plt.savefig(f_png)
                f_png.close()
                with open(fname, "rb") as image_file:
                    encoded_figure = base64.b64encode(image_file.read()).decode("ascii")
                os.remove(fname)
                # Add image/png MIME part
                body = body + "--" + mime_boundary + "\n"
                body = body + "Content-Type: image/png\n"
                body = body + "Content-Disposition: inline\n"
                body = body + "Content-Transfer-Encoding: base64\n\n"
                for i in range(0, len(encoded_figure), 76):
                    debut = i
                    fin = i + 75
                    if fin >= len(encoded_figure):
                        fin = len(encoded_figure) - 1
                    body = body + encoded_figure[debut : (fin + 1)] + "\n"

            # Send email
            try:
                error_list = smtp.sendmail(
                    self.email_from_addr,
                    self.email_to_addrs,
                    email_header + "\n" + body + "\n" + "--" + mime_boundary + "--\n",
                )
                if len(error_list) == 0:
                    success = True
            except smtplib.SMTPHeloError:
                print("SMTP Helo Error")
                pass
            except smtplib.SMTPRecipientsRefused:
                print("Some recipients have been rejected by SMTP server")
                pass
            except smtplib.SMTPSenderRefused:
                print("SMTP server refused sender " + self.email_from_addr)
                pass
            except smtplib.SMTPDataError:
                print("SMTP Data Error")
                pass

        else:
            try:
                email_content = (
                    email_header.encode("utf-8")
                    + b"\n"
                    + quopri.encodestring(self.email_body.encode("utf-8"))
                )
                error_list = smtp.sendmail(
                    self.email_from_addr, self.email_to_addrs, email_content
                )
                if len(error_list) == 0:
                    success = True
            except smtplib.SMTPHeloError:
                print("SMTP Helo Error")
                pass
            except smtplib.SMTPRecipientsRefused:
                print("Some recipients have been rejected by SMTP server")
                pass
            except smtplib.SMTPSenderRefused:
                print("SMTP server refused sender " + self.email_from_addr)
                pass
            except smtplib.SMTPDataError:
                print("SMTP Data Error")
                pass

        smtp.quit()
        self.email_body = ""
        self.email_started = False
        self.email_figlist = []
        if success:
            self.parameters["email_lastSent"] = time.time()
            date_string = time.strftime(
                dateformat, time.localtime(self.parameters["email_lastSent"])
            )
            print(date_string + ": Email successfully sent.")

    def time_since_last_email(self):
        try:
            last = self.parameters["email_lastSent"]
        except Exception:
            last = 0.0
            pass
        return time.time() - last

    def Stop(self):
        if self.email_started:
            self.stop_email()
            print("MI: email stopped.")
        if self.opened:
            self.store.close()
            self.datfile.close()
            date_string = time.strftime(dateformat, time.localtime(time.time()))
            self.logfile.write("Session closed on " + date_string)

            self.logfile.flush()
            self.logfile.close()
            self.opened = False
            print("MI: Successfully ended.")

    def __exit__(self, t, v, cb):
        self.Stop()
        super(Session, self).__exit__(t, v, cb)

    def __del__(self):
        if hasattr(self, "exited"):
            # let __enter__/__exit__ call self.Stop()
            pass
        else:
            # not inside a with statement, calling Stop when
            # object is being deleted
            self.Stop()
