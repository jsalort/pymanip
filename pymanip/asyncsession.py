"""

This module defines another kind of session, meant to be used for asynchronous
monitoring, where each variable can be logged with its own timestamp.

"""

import sqlite3
from datetime import datetime
import warnings
import numpy as np
import matplotlib.pyplot as plt

__all__ = ['AsyncSession']


class AsyncSession:

    def __init__(self, session_name, variable_list=None):
        if variable_list is None:
            variable_list = []
        self.conn = sqlite3.connect(session_name + '.db')
        with self.conn as c:
            tables = list(c.execute("SELECT name FROM sqlite_master;"))
            if not tables:
                c.execute("""
                    CREATE TABLE log (
                    timestamp INT,
                    name TEXT,
                    value REAL);
                    """)
                c.execute("""
                    CREATE TABLE parameters (
                        name TEXT,
                        value REAL);
                    """)

    def __enter__(self):
        return self

    def __exit__(self, type_, value, cb):
        self.conn.close()

    def add_entry(self, **kwargs):
        with self.conn as c:
            for key, val in kwargs.items():
                c.execute('INSERT INTO log VALUES (?,?,?)',
                          (datetime.now().timestamp(), key, val))

    def logged_variables(self):
        with self.conn as conn:
            c = conn.cursor()
            c.execute('SELECT name FROM log')
            data = set([d[0] for d in c.fetchall()])
        return data

    def save_parameter(self, **kwargs):
        with self.conn as conn:
            c = conn.cursor()
            for key, val in kwargs.items():
                c.execute('SELECT rowid FROM parameters WHERE name=?', key)
                rowid = c.fetchone()[0]
                print(rowid)
                if rowid is not None:
                    c.execute("""
                        REPLACE INTO parameters
                        (rowid, name, value)
                        VALUES (?,?,?)
                        """, (rowid, key, val))
                else:
                    c.execute("""
                        INSERT INTO parameters
                        (name, value)
                        VALUES (?,?)
                        """, (key, val))

    def parameter(self, name):
        with self.conn as conn:
            c = conn.cursor()
            c.execute('SELECT * FROM parameters WHERE name=?', name)
            data = c.fetchone()
            if data:
                return data['value']
        return None

    def has_parameter(self, name):
        return self.parameter(name) is not None

    def parameters(self):
        with self.conn as conn:
            c = conn.cursor()
            c.execute('SELECT * FROM parameters')
            data = c.fetchall()
        return {d[0]: d[1] for d in data}

    def __getitem__(self, key):
        with self.conn as conn:
            c = conn.cursor()
            c.execute('SELECT timestamp, value FROM log WHERE name=?', key)
            data = c.fetchall()
        t = np.array([d[0] for d in data])
        v = np.array([d[1] for d in data])
        return t, v

    def plot(self, name, num=1):
        ts, vs = self[name]
        plt.figure(num)
        plt.clf()
        plt.ion()
        plt.plot(ts-ts[0], vs, label=name)
        plt.legend(loc='upper left')
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            plt.pause(0.0001)


if __name__ == '__main__':
    with AsyncSession('Essai') as sesn:
        sesn.add_entry(a=1, b=2)
        sesn.save_parameter(c=3)
        sesn.plot('a')
