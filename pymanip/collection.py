#! /usr/bin/env python
# -*- coding: utf-8 -*-

from pymanip import SavedSession

class Manip(object):
    def __init__(self, session_name, nickname=None, **kwargs):
        self.properties = dict()
        for key in kwargs:
            self.properties[key] = kwargs[key]
        self.session_name = session_name
        if nickname:
            self.nickname = nickname
        else:
            self.nickname = session_name

    def __str__(self):
        return self.nickname

    def get(self, name):
        """
        Lookup for parameter of given name, first within the Manip object
        properties, and then inside the saved parameters of the specified
        session.
        """

        value = None
        if name == 'basename' or name == 'session_name':
            value = self.session_name
        elif name == 'nickname':
            value = self.nickname
        elif self.properties.has_key(name):
            value = self.properties[name]
        else:
            if self.MI.has_log(name):
                value = self.MI.log(name)
            elif self.MI.has_dataset(name):
                value = self.MI.dataset(name)
            elif self.MI.has_parameter(name):
                value = self.MI.parameter(name)
            else:
                value = None
                
        return value

    def __getitem__(self, key):
        return self.get(key)

    @property
    def MI(self):
        if not hasattr(self, '_MI'):
            self._MI = SavedSession(self.session_name)
        return self._MI

class ManipCollection(Manip):
    def __init__(self, basename, nickname=None, **kwargs):
        super(ManipCollection, self).__init__(session_name=basename, nickname=nickname, **kwargs)
        self.basename = basename
        if 'num' in kwargs:
            self.num = kwargs['num']
        else:
            self.num = 1

    def __getitem__(self, key):
        if isinstance(key, str):
            return super(ManipCollection, self).__getitem__(key)
        else:
            try:
                MI = SavedSession(self.basename + '_' + str(key))
            except IOError:
                print self.basename + '_' + str(key), 'does not exist'
                raise IndexError
            return MI

    def __iter__(self):
        self.current_acq = 1
        return self

    def next(self):
        c = self.current_acq
        self.current_acq = c+1
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

    def __iter__(self):
        return self.manips.__iter__()

    def __getitem__(self, key):
        if isinstance(key, str):
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
