#! /usr/bin/env python
# -*- coding: utf-8 -*-

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
        if self.properties.has_key(name):
            value = self.properties[name]
        else:
            with SavedSession(self.session_name) as MI:
                value = MI.parameter(name)
                
        return value
