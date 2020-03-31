"""
Module for legacy OctMI sessions

The OctSession class is designed to be used
in a similar fashion to SavedSession for
use by the collection classes.

"""

import os.path
import inspect
import h5py

from fluiddyn.util.terminal_colors import cprint
from .octmi_binary import read_OctMI_session


class OctSession(object):
    def __init__(
        self, session_name, cache_override=False, cache_location=".", verbose=False
    ):
        self.session_name = session_name
        self.variables = read_OctMI_session(session_name, verbose=verbose)
        self.time = self.variables.pop("t")
        self.cachestorename = (
            os.path.join(
                os.path.realpath(cache_location),
                "cache",
                os.path.basename(self.session_name),
            )
            + ".hdf5"
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

    def __str__(self):
        return self.session_name

    def describe(self):
        if len(self.variables) > 0:
            print("List of saved variables: (%d lines)" % len(self.time))
            for key, var in self.variables.items():
                print(" " + key)

    def has_dataset(self, name):
        return False

    def dataset(self, name):
        return None

    def has_parameter(self, name):
        return False

    def parameter(self, name):
        return None

    def has_log(self, name):
        if name in ["Time", "time", "t"]:
            return True
        return name in self.variables.keys()

    def log_variable_list(self):
        return self.variables.keys()

    def log(self, varname):
        if varname in ["Time", "time", "t"]:
            return self.time
        elif varname == "?":
            print(self.log_variable_list())
        elif varname in self.variables:
            return self.variables[varname]
        else:
            cprint.red("Variable is not defined: " + varname)

    def __getitem__(self, key):
        return self.log(key)

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
            cprint.yellow("Retriving " + varname + " from cache")
            return self.cachestore[varname].value
        else:
            return None

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

    def __del__(self):
        if hasattr(self, "has_cachestore") and self.has_cachestore:
            self.cachestore.close()
