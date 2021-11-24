"""Asynchronous Session Module (:mod:`pymanip.asyncsession`)
============================================================

This module defines two classes for live acquisition, :class:`~pymanip.asyncsession.AsyncSession`
and :class:`~pymanip.asyncsession.RemoteObserver`. The former is used to
manage an experimental session, the latter to access its live data from a
remote computer. There is also one class for read-only access to previous session,
:class:`~pymanip.asyncsession.SavedAsyncSession`.

.. autoclass:: AsyncSession
   :members:
   :private-members:

.. autoclass:: SavedAsyncSession
   :members:
   :private-members:

.. autoclass:: RemoteObserver
   :members:
   :private-members:

.. _FluidLab: https://foss.heptapod.net/fluiddyn/fluidlab

"""

import signal
import time
import sys
import os.path
import pickle
import warnings
import inspect
from pprint import pprint
from functools import lru_cache

try:
    from functools import cached_property
except ImportError:
    from backports.cached_property import cached_property

import sqlite3
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.cbook import mplDeprecation as MatplotlibDeprecationWarning

import asyncio
from aiohttp import web
import aiohttp_jinja2
import jinja2
import tempfile
import smtplib
from email.message import EmailMessage
import requests
import json

try:
    import PyQt5.QtCore
except (ModuleNotFoundError, FileNotFoundError):
    pass

from fluiddyn.util.terminal_colors import cprint
from pymanip.mytime import dateformat

__all__ = ["AsyncSession"]


class AsyncSession:
    """This class represents an asynchronous experiment session. It is the main tool that we
    use to set up monitoring of experimental systems. It will manage the storage for the data,
    as well as several asynchronous functions for use during the monitoring of the experimental
    system such as live plot of monitored data, regular control email, and remote HTTP access to
    the live data by human (connection from a web browser), or by a machine using the
    :class:`pymanip.asyncsession.RemoteObserver` class. It has methods to access the data for
    processing during the experiment, or post-processing after the experiment is finished.

    :param session_name: the name of the session, defaults to None. It will be used as the filename of the sqlite3 database file stored on disk. If None, then no file is created, and data will be temporarily stored in memory, but will be lost when the object is released.
    :type session_name: str, optional
    :param verbose: sets the session verbosity, defaults to True
    :type verbose: bool, optional
    :param delay_save: if True, the data is stored in memory during the duration of the session, and is saved to disk only at the end of the session. It is not recommanded, but useful in cases where fast operation requires to avoid disk access during the session.
    :type delay_save: bool, optional
    """

    database_version = 3

    def __init__(
        self,
        session_name=None,
        verbose=True,
        delay_save=False,
        exist_ok=True,
        readonly=False,
    ):
        """Constructor method"""

        if session_name is not None:
            session_name = str(session_name)  # in case it is a Path object
            if session_name.endswith(".db"):
                session_name = session_name[:-3]
        elif delay_save:
            raise ValueError("Cannot delay_save if session_name is not specified")

        self.session_name = session_name
        self.verbose = verbose
        self.exist_ok = exist_ok
        self.readonly = readonly
        self.delay_save = delay_save

        self.custom_figures = None
        self.figure_list = []
        self.template_dir = os.path.join(os.path.dirname(__file__), "web")
        self.static_dir = os.path.join(os.path.dirname(__file__), "web_static")
        self.jinja2_loader = jinja2.FileSystemLoader(self.template_dir)
        self.conn = None

    def save_database(self):
        """This method is useful only if delay_save = True. Then, the database is kept in-memory for
        the duration of the session. This method saves the database on the disk.
        A new database file will be created with the content of the current
        in-memory database.

        This method is automatically called at the exit of the context manager.
        """
        if self.conn is None:
            raise RuntimeError("AsyncSession is not opened!")

        if self.delay_save:
            try:
                os.remove(str(self.session_name) + ".db")
            except FileNotFoundError:
                pass
            disk_db = sqlite3.connect(str(self.session_name) + ".db")
            try:
                with disk_db as c:
                    for line in self.conn.iterdump():
                        c.execute(line)
            finally:
                disk_db.close()

    def open(self):
        """Opens database for reading or writting"""

        if self.conn is not None:
            raise RuntimeError("Already opened!")

        if not self.exist_ok and os.path.exists(self.session_name + ".db"):
            raise RuntimeError("File exists !")

        if self.session_name is None or self.delay_save:
            # For no name session, or in case of delay_save=True, then
            # the connection is in-memory
            self.conn = sqlite3.connect(":memory:")
        else:
            # Otherwise, the connection is on the disk for immediate read/write
            if self.readonly:
                uri = "file:{path:}?mode=ro".format(path=self.session_name + ".db")
                self.conn = sqlite3.connect(uri, uri=True)
            else:
                self.conn = sqlite3.connect(self.session_name + ".db")

        if self.delay_save and os.path.exists(self.session_name + ".db"):
            # Load existing database into in-memory database
            uri = "file:{path:}?mode=ro".format(path=self.session_name + ".db")
            disk_db = sqlite3.connect(uri, uri=True)
            try:
                with self.conn as c:
                    for line in disk_db.iterdump():
                        c.execute(line)
            finally:
                disk_db.close()

        with self.conn as c:
            tables = list(c.execute("SELECT name FROM sqlite_master;"))
            if not tables:
                c.execute(
                    """
                    CREATE TABLE log_names (
                    name TEXT);
                    """
                )
                c.execute(
                    """
                    CREATE TABLE log (
                    timestamp INT,
                    name TEXT,
                    value REAL);
                    """
                )
                c.execute(
                    """
                    CREATE TABLE dataset_names (
                    name TEXT);
                    """
                )
                c.execute(
                    """
                    CREATE TABLE dataset (
                    timestamp INT,
                    name TEXT,
                    data BLOB);
                    """
                )
                c.execute(
                    """
                    CREATE TABLE parameters (
                        name TEXT,
                        value REAL);
                    """
                )
                c.execute(
                    """
                    INSERT INTO parameters
                    (name, value)
                    VALUES (?,?);
                    """,
                    ("_database_version", AsyncSession.database_version),
                )
                c.execute(
                    """
                    INSERT INTO parameters
                    (name, value)
                    VALUES (?,?);
                    """,
                    ("_session_creation_timestamp", datetime.now().timestamp()),
                )
            elif self.verbose:
                self.print_welcome()

    def close(self):
        if self.conn:
            self.save_database()
            self.conn.close()
        self.conn = None

    def __enter__(self):
        """Context manager enter method"""
        if not self.conn:
            self.open()
        return self

    def __exit__(self, type_, value, cb):
        """Context manager exit method"""
        self.close()

    def get_version(self):
        """Returns current version of the database layout."""
        version = self.parameter("_database_version")
        if version is None:
            version = 1
        return version

    @cached_property
    def t0(self):
        """Session creation timestamp"""
        t0 = self.parameter("_session_creation_timestamp")
        if t0 is not None:
            return t0
        logged_data = self.logged_first_values()
        if logged_data:
            t0 = min([v[0] for k, v in logged_data.items()])
            self.save_parameter(_session_creation_timestamp=t0)
            return t0
        return 0

    @property
    def initial_timestamp(self):
        """Session creation timestamp, identical to :attr:`pymanip.asyncsession.AsyncSession.t0`"""
        return self.t0

    @property
    def last_timestamp(self):
        """Timestamp of the last recorded value"""
        ts = list()
        last_values = self.logged_last_values()
        if last_values:
            ts.append(max([t_v[0] for name, t_v in last_values.items()]))
        for ds_name in self.dataset_names():
            ts.append(max(self.dataset_times(ds_name)))
        if ts:
            return max(ts)
        return None

    def print_welcome(self):
        """Prints informative start date/end date message. If verbose is True, this method
        is called by the constructor.
        """
        start_string = time.strftime(dateformat, time.localtime(self.initial_timestamp))
        cprint.blue("*** Start date: " + start_string)
        last = self.last_timestamp
        if last:
            end_string = time.strftime(dateformat, time.localtime(last))
            cprint.blue("***   End date: " + end_string)

    def print_description(self):
        """Prints the list of parameters, logged variables and datasets."""
        version = self.get_version()
        print(
            self.session_name,
            "is an asynchroneous session (version {:}).".format(version),
        )
        print()
        last_values = self.logged_last_values()
        params = {
            key: val
            for key, val in self.parameters().items()
            if not key.startswith("_")
        }
        if params:
            print("Parameters")
            print("==========")
            for key, val in self.parameters().items():
                print(key, ":", val)
            print()

        if last_values:
            print("Logged variables")
            print("================")
            for name, t_v in last_values.items():
                print(name, "(", t_v[1], ")")
            print()

        ds_names = self.dataset_names()
        if ds_names:
            print("Datasets")
            print("========")
            for ds in ds_names:
                print(ds)
            print()

    def add_entry(self, *args, **kwargs):
        """This methods adds scalar values into the database. Each entry value
        will hold a timestamp corresponding to the time at which this method has been called.
        Variables are passed in dictionnaries or as keyword-arguments. If several variables
        are passed, then they all hold the same timestamps.

        For parameters which consists in only one scalar value, and for which timestamps are
        not necessary, use :meth:`pymanip.asyncsession.AsyncSession.save_parameter` instead.

        :param \\*args: dictionnaries with name-value to be added in the database
        :type \\*args: dict, optional
        :param \\**kwargs: name-value to be added in the database
        :type \\**kwargs: float, optional
        """
        ts = datetime.now().timestamp()
        data = dict()
        for a in args:
            data.update(a)
        data.update(kwargs)
        with self.conn as c:
            cursor = c.cursor()
            cursor.execute("SELECT name FROM log_names;")
            names = set([d[0] for d in cursor.fetchall()])
            for key, val in data.items():
                if key not in names:
                    c.execute("INSERT INTO log_names VALUES (?);", (key,))
                    names.add(key)
                c.execute("INSERT INTO log VALUES (?,?,?);", (ts, key, val))

    def add_dataset(self, *args, **kwargs):
        """This method adds arrays, or other pickable objects, as “datasets” into the
        database. They will hold a timestamp corresponding to the time at which the method
        has been called.

        :param \\*args: dictionnaries with name-value to be added in the database
        :type \\*args: dict, optional
        :param \\**kwargs: name-value to be added in the database
        :type \\**kwargs: object, optional
        """
        ts = datetime.now().timestamp()
        data = dict()
        for a in args:
            data.update(a)
        data.update(kwargs)
        with self.conn as c:
            cursor = c.cursor()
            cursor.execute("SELECT name FROM dataset_names;")
            names = set([d[0] for d in cursor.fetchall()])
            for key, val in data.items():
                if key not in names:
                    c.execute("INSERT INTO dataset_names VALUES (?);", (key,))
                    names.add(key)
                c.execute(
                    "INSERT INTO dataset VALUES (?,?,?);",
                    (ts, key, pickle.dumps(val, protocol=4)),
                )

    def logged_variables(self):
        """This method returns a set of the names of the scalar variables currently stored
        in the session database.

        :return: names of scalar variables
        :rtype: set
        """
        with self.conn as conn:
            c = conn.cursor()
            c.execute("SELECT name FROM log_names;")
            data = c.fetchall()
        names = set([d[0] for d in data])
        return names

    def logged_data(self):
        """This method returns a name-value dictionnary containing all scalar variables
        currently stored in the session database.

        :return: all scalar variable values
        :rtype: dict
        """
        names = self.logged_variables()
        result = dict()
        for name in names:
            result[name] = self.__getitem__(name)
        return result

    def logged_variable(self, varname):
        """This method retrieve the timestamps and values of a specified scalar variable.
        It is possible to use the sesn[varname] syntax as a shortcut.

        :param varname: name of the scalar variable to retrieve
        :type varname: str
        :return: timestamps and values
        :rtype: tuple (timestamps, values) of numpy arrays.

        :Exemple:

        >>> ts, val = sesn.logged_variable('T_Pt_bas')

        """
        with self.conn as conn:
            c = conn.cursor()
            c.execute(
                """
                      SELECT timestamp, value FROM log
                      WHERE name='{:}';
                      """.format(
                    varname
                )
            )
            data = c.fetchall()
        t = np.array([d[0] for d in data])
        v = np.array([d[1] for d in data])
        return t, v

    def logged_first_values(self):
        """This method returns a dictionnary holding the first logged value of all scalar
        variables stored in the session database.

        :return: first values
        :rtype: dict
        """
        with self.conn as conn:
            c = conn.cursor()
            c.execute("SELECT name FROM log_names;")
            names = set([d[0] for d in c.fetchall()])
            result = dict()
            for name in names:
                c.execute(
                    """SELECT timestamp, value FROM log
                             WHERE name='{:}'
                             ORDER BY timestamp ASC
                             LIMIT 1;
                          """.format(
                        name
                    )
                )
                result[name] = c.fetchone()
        return result

    def logged_last_values(self):
        """This method returns a dictionnary holding the last logged value of all scalar
        variables stored in the session database.

        :return: last logged values
        :rtype: dict
        """
        with self.conn as conn:
            c = conn.cursor()
            c.execute("SELECT name FROM log_names;")
            names = set([d[0] for d in c.fetchall()])
            result = dict()
            for name in names:
                c.execute(
                    """SELECT timestamp, value FROM log
                             WHERE name='{:}'
                             ORDER BY timestamp DESC
                             LIMIT 1;
                          """.format(
                        name
                    )
                )
                result[name] = c.fetchone()
        return result

    def logged_data_fromtimestamp(self, name, timestamp):
        """This method returns the timestamps and values of a given scalar variable, recorded
        after the specified timestamp.

        :param name: name of the scalar variable to be retrieved.
        :type name: str
        :param timestamp: timestamp from which to recover values
        :type timestamp: float
        :return: the timestamps, and values of the specified variable
        :rtype: tuple of two numpy arrays
        """
        with self.conn as conn:
            c = conn.cursor()
            c.execute(
                """SELECT timestamp, value FROM log
                         WHERE name='{:}' AND timestamp > {:}
                         ORDER BY timestamp ASC;
                      """.format(
                    name, timestamp
                )
            )
            data = c.fetchall()
        t = np.array([d[0] for d in data if d[1] is not None])
        v = np.array([d[1] for d in data if d[1] is not None])
        return t, v

    def dataset_names(self):
        """This method returns the names of the datasets currently stored in the session
        database.

        :return: names of datasets
        :rtype: set
        """
        with self.conn as conn:
            c = conn.cursor()
            try:
                c.execute("SELECT name from dataset_names;")
                data = c.fetchall()
            except sqlite3.OperationalError:
                return set()
        return set([d[0] for d in data])

    def datasets(self, name):
        """This method returns a generator which will yield all timestamps and datasets
        recorded under the specified name.
        The rationale for returning a generator instead of a list, is that each individual
        dataset may be large.

        :param name: name of the dataset to retrieve
        :type name: str

        :Exemple:

        - To plot all the recorded datasets named 'toto'

        >>> for timestamp, data in sesn.datasets('toto'):
        >>>    plt.plot(data, label=f'ts = {timestamp-sesn.t0:.1f}')

        - To retrieve a list of all the recorded datasets named 'toto'

        >>> datas = [d for ts, d in sesn.datasets('toto')]

        """
        with self.conn as conn:
            c = conn.cursor()
            try:
                c.execute("SELECT name from dataset_names;")
                data = c.fetchall()
            except sqlite3.OperationalError:
                data = set()
            names = set([d[0] for d in data])
            if name not in names:
                print("Possible dataset names are", names)
                raise ValueError(f'Bad dataset name "{name:}"')
            it = c.execute(
                """SELECT timestamp, data FROM dataset
                              WHERE name='{:}'
                              ORDER BY timestamp ASC;
                           """.format(
                    name
                )
            )
            for row in it:
                yield row[0], pickle.loads(row[1])

    def dataset_last_data(self, name):
        """This method returns the last recorded dataset under the specified name.

        :param name: name of the dataset to retrieve
        :type name: str
        :return: dataset value
        :rtype: object
        """
        last_ts = self.dataset_times(name)[-1]
        return last_ts, self.dataset(name, ts=last_ts)

    def dataset_times(self, name):
        """This method returns the timestamp of the recorded dataset under the specified
        name.

        :param name: name of the dataset to retrieve
        :type name: str
        :return: array of timestamps
        :rtype: :class:`numpy.ndarray`
        """
        with self.conn as conn:
            c = conn.cursor()
            it = c.execute(
                """SELECT timestamp FROM dataset
                              WHERE name='{:}'
                              ORDER BY timestamp ASC;
                           """.format(
                    name
                )
            )
            t = np.array([v[0] for v in it])
        return t

    def dataset(self, name, ts=None, n=None):
        """This method returns the dataset recorded at the specified timestamp, and under
        the specified name.

        :param name: name of the dataset to retrieve
        :type name: str
        :param ts: timestamp at which the dataset was stored, defaults to the timestamp of the last recorded dataset under that name
        :type ts: float, optional
        :param n: select the nth dataset (in dataset timestamp chronological order)
        :type n: int, optional
        :return: the value of the recorded dataset
        :rtype: object
        """

        if ts is None:
            if n is None:
                ts, data = self.dataset_last_data(name)
                return data
            else:
                ts = self.dataset_times(name)[n]
        with self.conn as conn:
            c = conn.cursor()
            c.execute(
                """SELECT data FROM dataset
                         WHERE name='{:}' AND timestamp='{:}';
                      """.format(
                    name, ts
                )
            )
            data = pickle.loads(c.fetchone()[0])
        return data

    def save_parameter(self, *args, **kwargs):
        """This methods saves a scalar parameter into the database. Unlike scalar values
        saved by the :meth:`pymanip.asyncsession.AsyncSession.add_entry` method, such parameter
        can only hold one value, and does not have an associated timestamp.
        Parameters can be passed as dictionnaries, or keyword arguments.

        :param \\*args: dictionnaries with name-value to be added in the database
        :type \\*args: dict, optional
        :param \\**kwargs: name-value to be added in the database
        :type \\**kwargs: float, optional
        """
        data = dict()
        for a in args:
            data.update(a)
        data.update(kwargs)
        with self.conn as conn:
            c = conn.cursor()
            for key, val in data.items():
                c.execute(
                    """SELECT rowid FROM parameters
                             WHERE name='{:}';
                          """.format(
                        key
                    )
                )
                rowid = c.fetchone()
                if rowid is not None:
                    rowid = rowid[0]
                    c.execute(
                        """
                        REPLACE INTO parameters
                        (rowid, name, value)
                        VALUES (?,?,?);
                        """,
                        (rowid, key, val),
                    )
                else:
                    c.execute(
                        """
                        INSERT INTO parameters
                        (name, value)
                        VALUES (?,?);
                        """,
                        (key, val),
                    )

    def parameter(self, name):
        """This method retrieve the value of the specified parameter.

        :param name: name of the parameter to retrieve
        :type name: str
        :return: value of the parameter
        :rtype: float
        """
        with self.conn as conn:
            c = conn.cursor()
            c.execute(
                """
                      SELECT value FROM parameters
                      WHERE name='{:}';
                      """.format(
                    name
                )
            )
            data = c.fetchone()
            if data:
                return data[0]
        return None

    def has_parameter(self, name):
        """This method returns True if specified parameter exists in the session database.

        :param name: name of the parameter to retrieve
        :type name: str
        :return: True if parameter exists, False if it does not
        :rtype: bool
        """
        return self.parameter(name) is not None

    def parameters(self):
        """This method returns all parameter name and values.

        :return: parameters
        :rtype: dict
        """
        with self.conn as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM parameters;")
            data = c.fetchall()
        return {d[0]: d[1] for d in data}

    def __getitem__(self, key):
        """Implement the evaluation of self[varname] as a shortcut to obtain timestamp and values for a given
        variable name.
        """
        return self.logged_variable(key)

    async def send_email(
        self,
        from_addr,
        to_addrs,
        host,
        port=None,
        subject=None,
        delay_hours=6,
        initial_delay_hours=None,
        use_ssl_submission=False,
        use_starttls=False,
        user=None,
        password=None,
    ):
        """This method returns an asynchronous task which sends an email at regular intervals.
        Such a task should be passed to :meth:`pymanip.asyncsession.AsyncSession.monitor` or
        :meth:`pymanip.asyncsession.AsyncSession.run`, and does not have to be awaited manually.

        :param from_addr: email address of the sender
        :type from_addr: str
        :param to_addrs: email addresses of the recipients
        :type to_addrs: list of str
        :param host: hostname of the SMTP server
        :type host: str
        :param port: port number of the SMTP server, defaults to 25
        :type port: int, optional
        :param delay_hours: interval between emails, defaults to 6 hours
        :type delay_hours: float, optional
        :param initial_delay_hours: time interval before the first email is sent, default to None (immediately)
        :type initial_delay_hours: float, optional
        """

        if port is None:
            if use_ssl_submission:
                port = 465
            elif use_starttls:
                # Tough some servers can do starttls on port 25, but then the user must specify port=25
                # as this is less common than on the submission port.
                port = 587
            else:
                port = 25
        if self.session_name is None:
            title = "Pymanip session"
        else:
            title = self.session_name
        if subject is None:
            subject = title

        if initial_delay_hours is None:
            initial_delay_hours = delay_hours / 2

        if initial_delay_hours > 0:
            await self.sleep(initial_delay_hours * 3600, verbose=False)

        jinja2_autoescape = jinja2.select_autoescape(["html"])
        jinja2_env = jinja2.Environment(
            loader=self.jinja2_loader, autoescape=jinja2_autoescape
        )
        template = jinja2_env.get_template("email.html")

        while self.running:

            dt_n = datetime.now()
            dt_fmt = "{:}{:02d}{:02d}-{:02d}{:02d}{:02d}"
            datestr = dt_fmt.format(
                dt_n.year, dt_n.month, dt_n.day, dt_n.hour, dt_n.minute, dt_n.second
            )
            # Generate HTML content
            last_values = self.logged_last_values()
            for name in last_values:
                timestamp, value = last_values[name]
                last_values[name] = (
                    timestamp,
                    value,
                    time.strftime(dateformat, time.localtime(timestamp)),
                )
            n_figs = len(self.figure_list)
            message_html = template.render(
                title=title,
                fignums=range(n_figs),
                datestr=datestr,
                last_values=last_values,
                variable_names=sorted(last_values.keys()),
            )

            # Create Email message
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = from_addr
            msg["To"] = to_addrs
            msg.set_content("This is a MIME message")
            msg.add_alternative(message_html, subtype="html")

            # Add figure images
            for fignum, fig in enumerate(self.figure_list):
                fd, fname = tempfile.mkstemp(suffix=".png")
                with os.fdopen(fd, "wb") as f_png:
                    fig.canvas.draw_idle()
                    fig.savefig(f_png)
                with open(fname, "rb") as image_file:
                    figure_data = image_file.read()
                os.remove(fname)
                p = msg.get_payload()[1]
                p.add_related(
                    figure_data,
                    maintype="image",
                    subtype="png",
                    cid="{:d}{:}".format(fignum, datestr),
                    filename="fig{:d}-{:}.png".format(fignum, datestr),
                )

            try:
                if use_ssl_submission:
                    smtp_server = smtplib.SMTP_SSL(host, port)
                else:
                    smtp_server = smtplib.SMTP(host, port)
            except Exception as e:
                print("Unable to connect to SMTP server")
                print(e)
                await self.sleep(60, verbose=False)
                continue

            with smtp_server as smtp:
                if use_starttls:
                    smtp.starttls()
                if user and password:
                    if not use_starttls and not use_ssl_submission:
                        raise RuntimeError(
                            "Do you really want to send password unencrypted?"
                        )
                    try:
                        smtp.login(user, password)
                    except smtplib.SMTPHeloError:
                        print("The server didn’t reply properly to the HELO greeting.")
                    except smtplib.SMTPAuthenticationError:
                        print(
                            "The server didn’t accept the username/password combination."
                        )
                    except smtplib.SMTPNotSupportedError:
                        print("The AUTH command is not supported by the server.")
                try:
                    smtp.send_message(msg)
                    print("Email sent!")
                except smtplib.SMTPHeloError:
                    print("SMTP Helo Error")
                except smtplib.SMTPRecipientsRefused:
                    print("Some recipients have been rejected by SMTP server")
                except smtplib.SMTPSenderRefused:
                    print("SMTP server refused sender " + self.email_from_addr)
                except smtplib.SMTPDataError:
                    print("SMTP Data Error")

            await self.sleep(delay_hours * 3600, verbose=False)

    async def plot(
        self,
        varnames=None,
        maxvalues=1000,
        yscale=None,
        *,
        x=None,
        y=None,
        fixed_ylim=None,
        fixed_xlim=None,
    ):
        """This method returns an asynchronous task which creates and regularly updates a plot for
        the specified scalar variables. Such a task should be passed to :meth:`pymanip.asyncsession.AsyncSession.monitor` or
        :meth:`pymanip.asyncsession.AsyncSession.run`, and does not have to be awaited manually.

        If varnames is specified, the variables are plotted against time. If x and y are specified, then
        one is plotted against the other.

        :param varnames: names of the scalar variables to plot
        :type varnames: list or str, optional
        :param maxvalues: number of values to plot, defaults to 1000
        :type maxvalues: int, optional
        :param yscale: fixed yscale for temporal plot, defaults to automatic ylim
        :type yscale: tuple or list, optional
        :param x: name of the scalar variable to use on the x axis
        :type x: str, optional
        :param y: name of the scalar variable to use on the y axis
        :type y: str, optional
        :param fixed_xlim: fixed xscale for x-y plots, defaults to automatic xlim
        :type fixed_xlim: tuple or list, optional
        :param fixed_ylim: fixed yscale for x-y plots, defaults to automatic ylim
        :type fixed_ylim: tuple or list, optional
        """
        if varnames is None:
            if not isinstance(x, str) or not isinstance(y, str):
                raise TypeError("x and y should be strings")
            varnames = (x, y)
            param_key_window = "_window_xy_" + "_".join(varnames)
            param_key_figsize = "_figsize_xy_" + "_".join(varnames)
            xymode = True
        else:
            if x is not None or y is not None:
                raise ValueError("Cannot specify both varnames and (x,y)")
            if isinstance(varnames, str):
                varnames = (varnames,)
            param_key_window = "_window_" + "_".join(varnames)
            param_key_figsize = "_figsize_" + "_".join(varnames)
            xymode = False
        last_update = {k: 0 for k in varnames}
        saved_geom = self.parameter(param_key_window)
        if saved_geom:
            saved_geom = eval(saved_geom)
        saved_figsize = self.parameter(param_key_figsize)
        if saved_figsize:
            saved_figsize = eval(saved_figsize)
        if not self.offscreen_figures:
            plt.ion()
        fig = plt.figure(figsize=saved_figsize)
        if not self.offscreen_figures:
            mngr = fig.canvas.manager
            if saved_geom:
                mngr.window.setGeometry(saved_geom)
        ax = fig.add_subplot(111)
        line_objects = dict()
        self.figure_list.append(fig)
        ts0 = self.initial_timestamp
        while self.running:
            data = {
                k: self.logged_data_fromtimestamp(k, last_update[k]) for k in varnames
            }
            if xymode:
                ts_x, vs_x = data[x]
                ts_y, vs_y = data[y]
                if (ts_x != ts_y).any():
                    raise ValueError(
                        "xymode can only be used if x and y are synchronous"
                    )
                if ts_x.size > 0:
                    if y in line_objects:
                        p = line_objects[y]
                        xx = np.hstack((p.get_xdata(), vs_x))
                        yy = np.hstack((p.get_ydata(), vs_y))
                        p.set_xdata(xx)
                        p.set_ydata(yy)
                        if fixed_xlim is None:
                            xlim = ax.get_xlim()
                            try:
                                if xlim[1] < np.max(xx) or xlim[0] > np.min(xx):
                                    ax.set_xlim((np.min(xx), np.max(xx)))
                            except TypeError:
                                pass
                        if fixed_ylim is None:
                            ylim = ax.get_ylim()
                            try:
                                if ylim[1] < np.max(yy) or ylim[0] > np.min(yy):
                                    ax.set_ylim((np.min(yy), np.max(yy)))
                            except TypeError:
                                pass
                    else:
                        (p,) = ax.plot(vs_x, vs_y, "s-")
                        line_objects[y] = p
                        ax.set_xlabel(x)
                        ax.set_ylabel(y)
                        if fixed_xlim is None:
                            try:
                                if np.min(vs_x) != np.max(vs_x):
                                    ax.set_xlim((np.min(vs_x), np.max(vs_x)))
                            except TypeError:
                                pass
                        else:
                            ax.set_xlim(fixed_xlim)
                        if fixed_ylim is None:
                            try:
                                if np.min(vs_y) != np.max(vs_y):
                                    ax.set_ylim((np.min(vs_y), np.max(vs_y)))
                            except TypeError:
                                pass
                        else:
                            ax.set_ylim(fixed_ylim)
                        if not self.offscreen_figures:
                            fig.show()
                    last_update[x] = ts_x[-1]
                    last_update[y] = ts_y[-1]
            else:
                for name, values in data.items():
                    ts, vs = values
                    if ts.size > 0:
                        if name in line_objects:
                            # print('updating plot')
                            p = line_objects[name]
                            x = np.hstack((p.get_xdata(), (ts - ts0) / 3600))
                            y = np.hstack((p.get_ydata(), vs))
                            if x.size > maxvalues:
                                x = x[-maxvalues:]
                                y = y[-maxvalues:]
                            p.set_xdata(x)
                            p.set_ydata(y)
                            if x[0] != x[-1]:
                                ax.set_xlim((x[0], x[-1]))
                            if fixed_ylim is None:
                                ylim = ax.get_ylim()
                                if ylim[1] < np.max(y) or ylim[0] > np.min(y):
                                    ylim = (
                                        min((ylim[0], np.min(y))),
                                        max((ylim[1], np.max(y))),
                                    )
                                    ax.set_ylim(ylim)
                        else:
                            # print('initial plot')
                            x = (ts - ts0) / 3600
                            y = vs
                            if x.size > maxvalues:
                                x = x[-maxvalues:]
                                y = y[-maxvalues:]
                            (p,) = ax.plot(x, y, "o-", label=name)
                            line_objects[name] = p
                            ax.set_xlabel("t [h]")
                            if x[0] != x[-1]:
                                ax.set_xlim((x[0], x[-1]))
                            if yscale:
                                ax.set_yscale(yscale)
                            if fixed_ylim is not None:
                                ax.set_ylim(fixed_ylim)
                            ax.legend()
                            if not self.offscreen_figures:
                                fig.show()
                        last_update[name] = ts[-1]
            await asyncio.sleep(1)

        if not self.offscreen_figures:
            # Saving figure positions
            try:
                geom = mngr.window.geometry()
                figsize = tuple(fig.get_size_inches())
                self.save_parameter(
                    **{param_key_window: str(geom), param_key_figsize: str(figsize)}
                )
            except AttributeError:
                pass

    async def figure_gui_update(self):
        """This method returns an asynchronous task which updates the figures created by the
        :meth:`pymanip.asyncsession.AsyncSession.plot` tasks. This task is added automatically,
        and should not be used manually.
        """
        if not self.offscreen_figures:
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=MatplotlibDeprecationWarning)
                while self.running:
                    figure_list = self.figure_list
                    if self.custom_figures:
                        figure_list = figure_list + self.custom_figures
                    if figure_list:
                        for fig in self.figure_list:
                            fig.canvas.start_event_loop(0.7 / len(self.figure_list))
                            await asyncio.sleep(0.3 / len(self.figure_list))
                        await asyncio.sleep(0.05)
                    else:
                        await asyncio.sleep(1.0)
        else:
            await asyncio.sleep(0.0)

    def ask_exit(self, *args, **kwargs):
        """This methods informs all tasks that the monitoring session should stop. Call this method if you
        wish to cleanly stop the monitoring session. It is also automatically called if the interrupt signal
        is received.
        It essentially sets the :attr:`running` attribute to False.
        Long user-defined tasks should check the :attr:`running` attribute, and abort if set to False.
        All other AsyncSession tasks check the attribute and will stop. The :meth:`~pymanip.asyncsession.AsyncSession.sleep`
        method also aborts sleeping.
        """
        self.running = False
        print(" Signal caught... stopping...")

    async def sweep(self, task, iterable):
        """This methods returns an asynchronous task which repeatedly awaits a given co-routine by iterating
        the specified iterable. The returned asynchronous task should be passed to :meth:`pymanip.asyncsession.AsyncSession.monitor` or
        :meth:`pymanip.asyncsession.AsyncSession.run`, and does not have to be awaited manually.

        This should be used when the main task of the asynchronous session is to sweep some value. The asynchronous session
        will exit when all values have been iterated.
        This is similar to running a script which consists in a synchronous for-loop, except that other tasks, such as remote
        access, live-plot and emails can be run concurrently.

        :param task: the co-routine function to repeatedly call and await
        :type task: function
        :param iterable: values to pass when calling the function
        :type iterable: list

        :Example:

        >>> async def balayage(sesn, voltage):
        >>>     await sesn.generator.vdc.aset(voltage)
        >>>     await asyncio.sleep(5)
        >>>     response = await sesn.multimeter.aget(channel)
        >>>     sesn.add_entry(voltage=voltage, response=response)
        >>>
        >>> async def main(sesn):
        >>>     await sesn.monitor(sesn.sweep(balayage, [0.0, 1.0, 2.0]))
        >>>
        >>> asyncio.run(main(sesn))

        """
        for val in iterable:
            await task(self, val)
            if not self.running:
                break
        self.running = False

    async def sleep(self, duration, verbose=True):
        """This method returns an asynchronous task which waits the specified amount of time and
        prints a countdown. This should be called with verbose=True by only one of the tasks.
        The other tasks should call with verbose=False.
        This method should be preferred over asyncio.sleep because it checks that
        :meth:`pymanip.asyncsession.AsyncSession.ask_exit` has not been called, and stops waiting
        if it has. This is useful to allow rapid abortion of the monitoring session.

        :param duration: time to wait
        :type duration: float
        :param verbose: whether to print the countdown, defaults to True
        :type verbose: bool, optional
        """
        start = time.monotonic()
        while self.running and time.monotonic() - start < duration:
            if verbose:
                print(
                    "Sleeping for "
                    + str(-int(time.monotonic() - start - duration))
                    + " s"
                    + " " * 8,
                    end="\r",
                )
                sys.stdout.flush()
            await asyncio.sleep(0.5)
        if verbose:
            sys.stdout.write("\n")

    async def server_main_page(self, request):
        """This asynchronous method returns the HTTP response to a request for the main html web page.
        Should not be called manually.
        """
        print("[", datetime.now(), request.remote, request.rel_url, "]")
        if self.session_name:
            context = {"title": self.session_name}
        else:
            context = {"title": "pymanip"}
        response = aiohttp_jinja2.render_template("main.html", request, context)
        return response

    async def server_logged_last_values(self, request):
        """This asynchronous method returns the HTTP response to a request for JSON data of the last logged
        values. Should not be called manually.
        """
        data = [
            {
                "name": name,
                "value": str(v[1]) if isinstance(v[1], bytes) else v[1],
                "datestr": time.strftime(dateformat, time.localtime(v[0])),
            }
            for name, v in self.logged_last_values().items()
        ]
        return web.json_response(data)

    async def server_get_parameters(self, request):
        """This asynchronous method returns the HTTP response to a request for JSON data of the session
        parameters. Should not be called manually.
        """
        params = {
            k: (str(v) if isinstance(v, bytes) else v)
            for k, v in self.parameters().items()
            if not k.startswith("_")
        }
        return web.json_response(params)

    async def server_plot_page(self, request):
        """This asynchronous method returns the HTTP response to a request for the HTML plot page.
        Should not be called manually.
        """
        print("[", datetime.now(), request.remote, request.rel_url, "]")
        context = {"name": request.match_info["name"]}
        response = aiohttp_jinja2.render_template("plot.html", request, context)
        return response

    async def server_data_from_ts(self, request):
        """This asynchronous method returns the HTTP response to a request for JSON with all data
        after the specified timestamp. Should not be called manually.
        """
        data_in = await request.json()
        last_ts = data_in["last_ts"]
        name = data_in["name"]
        timestamps, values = self.logged_data_fromtimestamp(name, last_ts)
        data_out = list(zip(timestamps, values))
        # print('from', last_ts, data_out)
        return web.json_response(data_out)

    async def server_current_ts(self, request):
        """This asynchronous method returns the HTTP response to a request for JSON with the current
        server time. Should not be called manually.
        """
        return web.json_response({"now": datetime.now().timestamp()})

    async def mytask(self, corofunc):
        """This method repeatedly awaits the given co-routine function, as long as
        :meth:`pymanip.asyncsession.AsyncSession.ask_exit` has not been called.
        Should not be called manually.
        """
        print("Starting task", corofunc)
        sig = inspect.signature(corofunc)
        while self.running:
            if len(sig.parameters) == 1:
                await corofunc(self)
            else:
                await corofunc()
        print("Task finished", corofunc)

    async def monitor(
        self,
        *tasks,
        server_port=6913,
        custom_routes=None,
        custom_figures=None,
        offscreen_figures=False,
    ):
        """This method runs the specified tasks, and opens a web-server for remote access and set up the tasks to run
        matplotlib event loops if necessary. This is the main
        method that the main function of user program should await for. It is also responsible for setting up
        the signal handling and binding it to the ask_exit method.

        It defines a :attr:`running` attribute, which is finally set to False when the monitoring must stop. User can
        use the :meth:`~pymanip.asyncsession.AsyncSession.ask_exit` method to stop the monitoring. Time consuming
        user-defined task should check the :attr:`running` and abort if set to False.

        :param \\*tasks: asynchronous tasks to run: if the task is a co-routine function, it will be called repeatedly until ask_exit is called. If task is an awaitable it is called only once. Such an awaitable is responsible to check that ask_exit has not been called. Several such awaitables are provided: :meth:`pymanip.asyncsession.AsyncSession.send_email`, :meth:`pymanip.asyncsession.AsyncSession.plot` and :meth:`pymanip.asyncsession.AsyncSession.sweep`.
        :type \\*tasks: co-routine function or awaitable
        :param server_port: the network port to open for remote HTTP connection, defaults to 6913. If None, no server is created.
        :type server_port: int, optional
        :param custom_routes: additionnal aiohttp routes for the web-server, defaults to None
        :type custom_routes: co-routine function, optional
        :param custom_figures: additional matplotlib figure object that needs to run the matplotlib event loop
        :type custom_figures: :class:`matplotlib.pyplot.Figure`, optional
        :param offscreen_figures: if set, figures are not shown onscreen
        :type offscreen_figures: bool, optional
        """
        loop = asyncio.get_event_loop()
        self.custom_figures = custom_figures
        self.offscreen_figures = offscreen_figures

        # signal handling
        self.running = True
        if sys.platform == "win32":
            # loop.add_signal_handler raises NotImplementedError
            signal.signal(signal.SIGINT, self.ask_exit)
        else:
            for signame in ("SIGINT", "SIGTERM"):
                loop.add_signal_handler(getattr(signal, signame), self.ask_exit)

        # web server
        if server_port:
            app = web.Application(loop=loop)
            aiohttp_jinja2.setup(app, loader=self.jinja2_loader)
            app.router.add_routes(
                [
                    web.get("/", self.server_main_page),
                    web.get("/api/logged_last_values", self.server_logged_last_values),
                    web.get("/plot/{name}", self.server_plot_page),
                    web.static("/static", self.static_dir),
                    web.post("/api/data_from_ts", self.server_data_from_ts),
                    web.get("/api/server_current_ts", self.server_current_ts),
                    web.get("/api/get_parameters", self.server_get_parameters),
                ]
            )
            if custom_routes:
                app.router.add_routes(custom_routes)

            webserver = loop.create_server(
                app.make_handler(), host=None, port=server_port
            )

        # if any of the tasks submitted are coroutinefunctions instead of
        # coroutines, then assume they take only one argument (self)
        tasks_final = list()
        for t in tasks:
            if asyncio.iscoroutinefunction(t):
                tasks_final.append(self.mytask(t))
            elif asyncio.iscoroutine(t):
                tasks_final.append(t)
            else:
                raise TypeError("Coroutine or Coroutinefunction is expected")
        print("Starting event loop")
        if server_port:
            await asyncio.gather(webserver, self.figure_gui_update(), *tasks_final)
        else:
            await asyncio.gather(self.figure_gui_update(), *tasks_final)

    def run(
        self,
        *tasks,
        server_port=6913,
        custom_routes=None,
        custom_figures=None,
        offscreen_figures=False,
    ):
        """Synchronous call to :meth:`pymanip.asyncsession.AsyncSession.monitor`."""

        asyncio.run(
            self.monitor(
                *tasks,
                server_port=server_port,
                custom_routes=custom_routes,
                custom_figures=custom_figures,
                offscreen_figures=offscreen_figures,
            )
        )

    def save_remote_data(self, data):
        """This method saves the data returned by a :class:`pymanip.asyncsession.RemoteObserver` object into the current session database,
        as datasets and parameters.

        :param data: data returned by the :class:`pymanip.asyncsession.RemoteObserver` object
        :type data: dict
        """
        for k, v in data.items():
            # print(k,type(v),v)
            try:
                v[0]
                iterable = True
            except (TypeError, KeyError):
                iterable = False
            if iterable:
                # we are iterable
                self.add_dataset(**{k: v})
            else:
                # we are not iterable
                if isinstance(v, dict):
                    # non reduced data, v is a dictionnary with two keys, 't' and 'value'
                    self.add_dataset(**{k: v["value"]})
                    self.add_dataset(**{k + "_time": v["t"]})
                else:
                    try:
                        # data must be a scalar
                        float(v)
                    except TypeError:
                        print("skipping", k, type(v))
                        continue
                    self.save_parameter(**{k: v})


class RemoteObserver:
    """This class represents remote observers of a monitoring session. It connects to the server opened on a remote computer by
    :meth:`pymanip.asyncsession.AsyncSession.monitor`. The aim of an instance of RemoteObserver is to retrieve the data saved into
    the remote computer session database.

    :param host: hostname of the remote compute to connect to
    :type host: str
    :param port: port number to connect to, defaults to 6913
    :type port: int, optional
    """

    def __init__(self, host, port=6913):
        """Constructor method"""
        self.host = host
        self.port = port

    def _get_request(self, apiname):
        """Private method to send a GET request for the specified API name"""
        url = "http://{host:}:{port:}/api/{api:}".format(
            host=self.host, port=self.port, api=apiname
        )
        r = requests.get(url)
        try:
            return r.json()
        except json.decoder.JSONDecodeError:
            print(r.text)
            raise

    def _post_request(self, apiname, params):
        """Private method to send a POST request for the specified API name and params"""
        url = "http://{host:}:{port:}/api/{api:}".format(
            host=self.host, port=self.port, api=apiname
        )
        r = requests.post(url, json=params)
        try:
            return r.json()
        except json.decoder.JSONDecodeError:
            print(r.text)
            raise

    def get_last_values(self):
        """This method retrieve the last set of values from
        the remote monitoring session.

        :return: scalar variable last recorded values
        :rtype: dict
        """

        data = self._get_request("logged_last_values")
        return {d["name"]: d["value"] for d in data}

    def start_recording(self):
        """This method establishes the connection to the remote computer, and sets the
        start time for the current observation session.
        """
        self.server_ts_start = self._get_request("server_current_ts")["now"]
        data = self.get_last_values()
        self.remote_varnames = list(data.keys())

    def stop_recording(self, reduce_time=True, force_reduce_time=True):
        """This method retrieves all scalar variable data recorded saved by the remote
        computer since :meth:`pymanip.asyncsession.RemoteObserver.start_recording` established
        the connection.

        :param reduce_time: if True, try to collapse all timestamp arrays into a unique timestamp array. This is useful if the remote computer program only has one call to add_entry. Defaults to True.
        :type reduce_time: bool, optional
        :param force_reduce_time: bypass checks that all scalar values indeed have the same timestamps.
        :type force_reduce_time: bool, optional
        :return: timestamps and values of all data saved in the remote computed database since the call to :meth:`pymanip.asyncsession.RemoteObserver.start_recording`
        :rtype: dict
        """
        recordings = dict()
        for varname in self.remote_varnames:
            data = self._post_request(
                "data_from_ts",
                params={"name": varname, "last_ts": self.server_ts_start},
            )
            if len(data) > 0:
                recordings[varname] = {
                    "t": [d[0] for d in data],
                    "value": [d[1] for d in data],
                }
        if reduce_time:
            t = recordings[self.remote_varnames[0]]["t"]
            if (
                all([recordings[varname]["t"] == t for varname in recordings])
                or force_reduce_time
            ):
                recordings = {k: v["value"] for k, v in recordings.items()}
                recordings["time"] = t
            else:
                print("t =", t)
                pprint(
                    {
                        varname: recordings[varname]["t"] == t
                        for varname in self.remote_varnames
                    }
                )
        parameters = self._get_request("get_parameters")
        recordings.update(parameters)

        return recordings


class SavedAsyncSession:
    """This class implements the same methods as AsyncSession with readonly mode, but with
    caching enabled. Also, the file is opened on demand. No context manager is necessary.
    """

    def __init__(self, session_name, verbose=True):

        self.session_name = session_name
        self.verbose = verbose
        self.session = AsyncSession(session_name, verbose=False, readonly=True)
        if verbose:
            try:
                self.print_welcome()
            except sqlite3.OperationalError:
                print("Warning: unable to open database for session", session_name)

    def print_welcome(self):
        """Prints informative start date/end date message. If verbose is True, this method
        is called by the constructor.
        """
        start_string = time.strftime(dateformat, time.localtime(self.initial_timestamp))
        cprint.blue("*** Start date: " + start_string)
        last = self.last_timestamp
        if last:
            end_string = time.strftime(dateformat, time.localtime(last))
            cprint.blue("***   End date: " + end_string)

    def print_description(self):
        """Prints the list of parameters, logged variables and datasets."""
        version = self.get_version()
        print(
            self.session_name,
            "is an asynchroneous session (version {:}).".format(version),
        )
        print()
        last_values = self.logged_last_values()
        params = {
            key: val
            for key, val in self.parameters().items()
            if not key.startswith("_")
        }
        if params:
            print("Parameters")
            print("==========")
            for key, val in self.parameters().items():
                print(key, ":", val)
            print()

        if last_values:
            print("Logged variables")
            print("================")
            for name, t_v in last_values.items():
                print(name, "(", t_v[1], ")")
            print()

        ds_names = self.dataset_names()
        if ds_names:
            print("Datasets")
            print("========")
            for ds in ds_names:
                print(ds)
            print()

    # General attributes

    @lru_cache(maxsize=128)
    def get_version(self):
        with self.session as sesn:
            return sesn.get_version()

    @property
    def t0(self):
        with self.session as sesn:
            return sesn.t0

    @property
    def initial_timestamp(self):
        return self.t0

    @cached_property
    def last_timestamp(self):
        ts = list()
        last_values = self.logged_last_values()
        if last_values:
            ts.append(max([t_v[0] for name, t_v in last_values.items()]))
        for ds_name in self.dataset_names():
            ts.append(max(self.dataset_times(ds_name)))
        if ts:
            return max(ts)
        return None

    # Logged variables

    @lru_cache(maxsize=128)
    def logged_data(self):
        with self.session as sesn:
            return sesn.logged_data()

    def logged_variables(self):
        return set(self.logged_data().keys())

    def logged_variable(self, varname):
        return self.logged_data()[varname]

    @lru_cache(maxsize=128)
    def logged_last_values(self):
        last = dict()
        for name, data in self.logged_data().items():
            ts, val = data
            max_ts = np.max(ts)
            assert ts[-1] == max_ts
            last[name] = (ts[-1], val[-1])
        return last

    @lru_cache(maxsize=128)
    def logged_first_values(self):
        first = dict()
        for name, data in self.logged_data().items():
            ts, val = data
            min_ts = np.min(ts)
            assert ts[0] == min_ts
            first[name] = (ts[0], val[0])
        return first

    @lru_cache(maxsize=128)
    def logged_data_fromtimestamp(self, name, timestamp):
        ts, val = self.logged_variable(name)
        for ind, tt in enumerate(ts):
            if tt == timestamp:
                break
        else:
            raise ValueError("No logged data at specified timestamp")
        return val[ind]

    def __getitem__(self, key):
        return self.logged_variable(key)

    # Dataset

    @lru_cache(maxsize=128)
    def dataset_names(self):
        with self.session as sesn:
            return sesn.dataset_names()

    def datasets(self, name):
        with self.session as sesn:
            return sesn.datasets()

    def dataset_last_data(self, name):
        """This method returns the last recorded dataset under the specified name.

        :param name: name of the dataset to retrieve
        :type name: str
        :return: dataset value
        :rtype: object
        """
        last_ts = self.dataset_times(name)[-1]
        return last_ts, self.dataset(name, ts=last_ts)

    @lru_cache(maxsize=128)
    def dataset_times(self, name):
        with self.session as sesn:
            sesn.dataset_times(name)

    def dataset(self, name, ts=None, n=None):
        if ts is None:
            if n is None:
                ts, data = self.dataset_last_data(name)
                return data
            else:
                ts = self.dataset_times(name)[n]
        with self.session as sesn:
            return sesn.dataset(name, ts=ts, n=n)

    # Parameters

    @lru_cache(maxsize=128)
    def parameters(self):
        with self.session as sesn:
            return sesn.parameters()

    def parameter(self, name):
        return self.parameters()[name]

    def has_parameter(self, name):
        return name in self.parameters()


if __name__ == "__main__":
    with AsyncSession("Essai") as sesn:
        sesn.add_entry(a=1, b=2)
        sesn.save_parameter(c=3)
        sesn.plot("a")
