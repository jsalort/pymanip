#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

from pymanip import SavedSession
from pymanip.legacy_session import OctSession
import os
import six


class Manip(object):
    def __init__(
        self, session_name, nickname=None, directory=None, verbose=True, **kwargs
    ):
        self.properties = dict()
        for key in kwargs:
            self.properties[key] = kwargs[key]
        self.session_name = session_name
        if nickname:
            self.nickname = nickname
        else:
            self.nickname = session_name
        self.directory = directory
        self.verbose = verbose
        self.cachedvars = self.MI.cachedvars
        self.cached = self.MI.cached
        self.cachedvalue = self.MI.cachedvalue
        self.cache = self.MI.cache

    def __str__(self):
        return self.nickname

    def get(self, name):
        """
        Lookup for parameter of given name, first within the Manip object
        properties, and then inside the saved parameters of the specified
        session.
        """

        value = None
        if name == "basename" or name == "session_name":
            value = self.session_name
        elif name == "nickname":
            value = self.nickname
        elif name in self.properties:
            value = self.properties[name]
        else:
            if self.MI.has_log(name):
                value = self.MI.log(name)
            elif self.MI.has_dataset(name):
                value = self.MI.dataset(name)
            elif self.MI.has_parameter(name):
                value = self.MI.parameter(name)
            else:
                raise KeyError("Key not found {:s}".format(name))

        return value

    def dataset(self, name):
        return self.MI.dataset(name)

    def __getitem__(self, key):
        return self.get(key)

    def describe(self):
        self.MI.describe()

    @property
    def MI(self):
        if not hasattr(self, "_MI"):
            if self.directory:
                name = os.path.join(self.directory, self.session_name)
            else:
                name = self.session_name
            try:
                self._MI = SavedSession(name, verbose=self.verbose)
            except IOError as a:
                try:
                    self._MI = OctSession(name, verbose=self.verbose)
                except IOError as b:
                    print("None of the possible files can be found:")
                    print(" 1. {:}".format(a.filename))
                    print(" 2. {:}".format(b.filename))
                    raise IOError('Cannot open session "{:}" for reading'.format(name))
                # print('OctMI legacy mode')

        return self._MI


class ManipCollection(Manip):
    def __init__(self, basename, nickname=None, **kwargs):
        self.basename = basename
        self.num = kwargs.pop("num", 1)
        self.verbose = kwargs.pop("verbose", True)

        super(ManipCollection, self).__init__(
            session_name=basename, nickname=nickname, verbose=self.verbose, **kwargs
        )

    def __getitem__(self, key):
        if isinstance(key, six.string_types):
            return super(ManipCollection, self).__getitem__(key)
        else:
            try:
                if self.directory:
                    name = os.path.join(self.directory, self.basename + "_" + str(key))
                else:
                    name = self.basename + "_" + str(key)
                MI = SavedSession(name, verbose=self.verbose)
            except IOError as e:
                print('Unable to read file "' + str(e.filename) + "'.")
                print("Errno = " + str(e.errno))
                print("Message: " + str(e.message))
                raise IndexError
            return MI

    @property
    def MI(self):
        if hasattr(self, "current_acq"):
            return self[self.current_acq]
        return self[1]

    def items_from(self, start):
        # __iter__ est appelé dans tous les cas
        self.custom_start = start
        return self

    def __iter__(self):
        if hasattr(self, "custom_start"):
            self.current_acq = self.custom_start
            delattr(self, "custom_start")
        else:
            self.current_acq = 1
        return self

    def __next__(self):
        c = self.current_acq
        self.current_acq = c + 1
        if c > self.num:
            raise StopIteration
        else:
            return self.__getitem__(c)


class ManipList(object):
    def __init__(self, *args):
        if len(args) == 1:
            if isinstance(args[0], list):
                self.manips = args[0]
            else:
                self.manips = [args[0]]
        else:
            self.manips = args

    def __len__(self):
        return len(self.manips)

    def __iter__(self):
        return self.manips.__iter__()

    def __getitem__(self, key):
        if isinstance(key, six.string_types):
            return self.from_nickname(key)
        else:
            return self.manips.__getitem__(key)

    def from_nickname(self, nickname):
        return self.lookup(nickname=nickname)[0]

    def lookup(self, **kwargs):
        result = list()
        for m in self.manips:
            keep = True
            for key in kwargs:
                if m.get(key) != kwargs[key]:
                    keep = False
            if keep:
                result.append(m)
        return result
