"""Asynchronous session class (:mod:`pymanip.asyncsession.asyncsession`)
========================================================================

This module defines the class for live acquisition, :class:`~pymanip.asyncsession.asyncsession.AsyncSession`.
It is used to manage an experimental session.

.. autoclass:: AsyncSession
   :members:
   :private-members:

"""

from pathlib import Path
import signal
import time
import sys
import os.path
import pickle
import warnings
import inspect
import shutil

try:
    from functools import cached_property
except ImportError:
    from backports.cached_property import cached_property
from datetime import datetime
import asyncio

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import MatplotlibDeprecationWarning

from aiohttp import web
import aiohttp_jinja2
from aiofile import async_open
import jinja2
import tempfile
import smtplib
from email.message import EmailMessage

from sqlalchemy import create_engine, delete
from sqlalchemy.orm import sessionmaker
import sqlalchemy.exc

try:
    import PyQt5.QtCore  # noqa: F401
except (ModuleNotFoundError, FileNotFoundError):
    pass

from fluiddyn.util.terminal_colors import cprint
from pymanip.mytime import dateformat

import pymanip.asyncsession.database_v1 as dbv1
import pymanip.asyncsession.database_v3 as dbv3
import pymanip.asyncsession.database_v4 as dbv4

dblatest = dbv4


__all__ = ["AsyncSession"]


def get_db_module(Session):
    """Reads version of database of given Session class, and returns appropriate database schema module."""
    with Session() as sesn:
        try:
            version = (
                sesn.query(dbv3.Parameter.value)
                .filter_by(name="_database_version")
                .one_or_none()
            )
        except sqlalchemy.exc.MultipleResultsFound:
            print("Multiple _database_version found. Fallback to dbv3.")
            return dbv3
        if version is None:
            return dbv1
        else:
            (version,) = version
            if version == 1:
                """Identique au schéma v2, mais sans les tables `dataset` et `dataset_names`."""
                db = dbv1
            elif version == 2:
                """Identique au schéma v3 mais il n'y a pas la property `_session_creation_timestamp`."""
                db = dbv3
            elif version == 3 or version == 3.1:
                db = dbv3
            elif version >= 4:
                db = dbv4
            else:
                print(f"Unable to determine database version. Got <{version}>.")
                return dbv4
    return db


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

    def __init__(
        self,
        session_name=None,
        verbose=True,
        delay_save=False,
        exist_ok=True,
        readonly=False,
        database_version=-1,
    ):
        """Constructor method"""

        if session_name is not None:
            if isinstance(session_name, Path):
                self.session_path = session_name
                self.session_name = self.session_path.name
                if self.session_name.endswith(".db"):
                    self.Session_name = self.session_name[:-3]
            else:
                if not session_name.endswith(".db"):
                    self.session_path = Path(session_name + ".db")
                    self.session_name = session_name
                else:
                    self.session_path = Path(session_name)
                    self.session_name = session_name[:-3]
        else:
            self.session_name = None
            self.session_path = None
            if delay_save:
                raise ValueError("Cannot delay_save if session_name is not specified")

        if self.session_path is not None and not delay_save:
            if self.session_path.exists():
                if not exist_ok:
                    raise RuntimeError("File exists !")
                new_session = False
            else:
                new_session = True
            self.engine = create_engine(
                "sqlite:///" + str(self.session_path.absolute()),
                echo=False,
            )
        else:
            self.engine = create_engine(
                "sqlite://",
                echo=False,
            )
            new_session = True
        self.Session = sessionmaker(bind=self.engine)
        if new_session:
            if database_version == -1:
                self.db = dblatest
            elif database_version == 3 or database_version == 3.1:
                self.db = dbv3
            elif database_version == 4:
                self.db = dbv4
        else:
            self.db = get_db_module(self.Session)

        if delay_save:
            # Load existing database into in-memory database
            self.disk_engine = create_engine(
                "sqlite:///" + str(self.session_path.absolute()),
                echo=False,
            )
            self.disk_Session = sessionmaker(bind=self.disk_engine)
            if self.session_path.exists():
                self.db = get_db_module(self.disk_Session)
                self.db.create_tables(self.engine)
                with self.disk_Session() as input_session, self.Session() as output_session:
                    for table in self.db.table_list:
                        self.db.copy_table(input_session, output_session, table)

        self.verbose = verbose
        self.readonly = readonly
        self.delay_save = delay_save

        self.custom_figures = None
        self.figure_list = []
        self.egui_process = set()
        self.egui_process_obj = set()
        self.template_dir = os.path.join(os.path.dirname(__file__), "web")
        self.static_dir = os.path.join(os.path.dirname(__file__), "web_static")
        self.jinja2_loader = jinja2.FileSystemLoader(self.template_dir)
        self.conn = None

    def __enter__(self):
        """Context manager enter method"""
        if not self.readonly:
            new = self.db.create_tables(self.engine)
        else:
            new = False
        if self.verbose and not new:
            self.print_welcome()
        if new:
            with self.Session() as session:
                session.add(
                    self.db.Parameter(
                        name="_database_version",
                        value=self.db.database_version,
                    )
                )
                session.add(
                    self.db.Parameter(
                        name="_session_creation_timestamp",
                        value=datetime.now().timestamp(),
                    )
                )
                session.commit()
        return self

    def __exit__(self, type_, value, cb):
        """Context manager exit method"""
        if self.delay_save:
            self.save_database()

    def save_database(self):
        """This method is useful only if delay_save = True. Then, the database is kept in-memory for
        the duration of the session. This method saves the database on the disk.
        A new database file will be created with the content of the current
        in-memory database.

        This method is automatically called at the exit of the context manager.
        """
        if self.delay_save:
            self.db.create_tables(self.disk_engine)
            with self.Session() as input_session, self.disk_Session() as output_session:
                for table in self.db.table_list:
                    output_session.query(table).delete()
                    self.db.copy_table(input_session, output_session, table)

    def get_version(self):
        """Returns current version of the database layout."""
        version = self.parameter("_database_version")
        if version is None:
            version = self.db.database_version
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

        if version >= 4:
            meta = self.metadatas()
            if meta:
                print("Metadata")
                print("========")
                for name, val in meta.items():
                    print(name, ":", val)
                print()

        if version >= 4.1:
            figures = list(self.figures())
            if figures:
                print("Figures")
                print("=======")
                for f in figures:
                    print(f"Fig {f['fignum']}:", ",".join(f["variables"]))

    def figures(self):
        with self.Session() as session:
            for fig in session.query(self.db.Figure).all():
                q = session.query(self.db.FigureVariable.name).filter_by(
                    fignum=fig.fignum
                )
                names = [r.name for r in q.all()]
                yield {
                    "fignum": fig.fignum,
                    "maxvalues": fig.maxvalues,
                    "yscale": fig.yscale,
                    "ymin": fig.ymin,
                    "ymax": fig.ymax,
                    "variables": names,
                }

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
        if self.readonly:
            raise RuntimeError("Cannot add entry to readonly session")
        ts = time.time_ns() / 1e9
        data = dict()
        for a in args:
            data.update(a)
        data.update(kwargs)
        with self.Session() as session:
            names = {name for name, in session.query(self.db.LogName.name)}
            for key, val in data.items():
                if key not in names:
                    session.add(self.db.LogName(name=key))
                    names.add(key)
                # On windows the clock is sometimes not precise enough, and there may be the same value for ts, which
                # would cause a violation of the Unique constraint on (timestamp, name).
                while (
                    session.query(self.db.Log.timestamp)
                    .filter_by(timestamp=ts, name=key)
                    .one_or_none()
                ) is not None:
                    ts += 1e-6
                    # print("add a microsecond to ts, new ts =", ts)
                session.add(self.db.Log(timestamp=ts, name=key, value=val))
            session.commit()

    def add_dataset(self, *args, **kwargs):
        """This method adds arrays, or other pickable objects, as “datasets” into the
        database. They will hold a timestamp corresponding to the time at which the method
        has been called.

        :param \\*args: dictionnaries with name-value to be added in the database
        :type \\*args: dict, optional
        :param \\**kwargs: name-value to be added in the database
        :type \\**kwargs: object, optional
        """
        if self.readonly:
            raise RuntimeError("Cannot add dataset to readonly session")
        ts = datetime.now().timestamp()
        data = dict()
        for a in args:
            data.update(a)
        data.update(kwargs)
        with self.Session() as session:
            names = {name for name, in session.query(self.db.DatasetName.name)}
            for key, val in data.items():
                if key not in names:
                    session.add(self.db.DatasetName(name=key))
                    names.add(key)
                session.add(
                    self.db.Dataset(
                        timestamp=ts, name=key, data=pickle.dumps(val, protocol=4)
                    )
                )
            session.commit()

    def logged_variables(self):
        """This method returns a set of the names of the scalar variables currently stored
        in the session database.

        :return: names of scalar variables
        :rtype: set
        """
        with self.Session() as session:
            names = {name for name, in session.query(self.db.LogName.name)}
        return names

    def logged_data(self):
        """This method returns a name-value dictionnary containing all scalar variables
        currently stored in the session database.

        :return: all scalar variable values
        :rtype: dict
        """
        result = dict()
        with self.Session() as sesn:
            names = {name for name, in sesn.query(self.db.LogName.name)}
            for name in names:
                ts_val = np.array(
                    [
                        (timestamp, value)
                        for timestamp, value in sesn.query(
                            self.db.Log.timestamp, self.db.Log.value
                        ).filter_by(name=name)
                    ]
                )
                result[name] = ts_val[:, 0].astype(float), ts_val[:, 1]
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
        with self.Session() as session:
            ts_val = np.array(
                [
                    (timestamp, value)
                    for timestamp, value in session.query(
                        self.db.Log.timestamp, self.db.Log.value
                    ).filter_by(name=varname)
                ]
            )
        return ts_val[:, 0], ts_val[:, 1]

    def logged_first_values(self):
        """This method returns a dictionnary holding the first logged value of all scalar
        variables stored in the session database.

        :return: first values
        :rtype: dict
        """
        result = dict()
        with self.Session() as session:
            names = {name for name, in session.query(self.db.LogName.name)}
            for name in names:
                r = (
                    session.query(self.db.Log)
                    .filter_by(name=name)
                    .order_by(self.db.Log.timestamp.asc())
                    .first()
                )
                if r is not None:
                    result[name] = (r.timestamp, r.value)
                else:
                    result[name] = None
        return result

    def logged_last_values(self):
        """This method returns a dictionnary holding the last logged value of all scalar
        variables stored in the session database.

        :return: last logged values
        :rtype: dict
        """
        result = dict()
        with self.Session() as session:
            names = {name for name, in session.query(self.db.LogName.name)}
            for name in names:
                r = (
                    session.query(self.db.Log)
                    .filter_by(name=name)
                    .order_by(self.db.Log.timestamp.desc())
                    .first()
                )
                if r is not None:
                    result[name] = (r.timestamp, r.value)
                else:
                    result[name] = None
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
        with self.Session() as session:
            ts_val = np.array(
                [
                    (timestamp, value)
                    for timestamp, value in session.query(
                        self.db.Log.timestamp, self.db.Log.value
                    )
                    .filter_by(name=name)
                    .filter(self.db.Log.timestamp >= timestamp)
                    .order_by(self.db.Log.timestamp)
                ]
            )
            nrows = len(ts_val)
        if nrows > 0:
            return ts_val[:, 0], ts_val[:, 1]
        else:
            return np.array([]), np.array([])

    def dataset_names(self):
        """This method returns the names of the datasets currently stored in the session
        database.

        :return: names of datasets
        :rtype: set
        """
        with self.Session() as session:
            names = {name for name, in session.query(self.db.DatasetName.name)}
        return names

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
        with self.Session() as session:
            names = {name for name, in session.query(self.db.DatasetName.name)}
            if name not in names:
                print("Possible dataset names are", names)
                raise ValueError(f'Bad dataset name "{name:}"')
            for timestamp, data in (
                session.query(self.db.Dataset.timestamp, self.db.Dataset.data)
                .filter_by(name=name)
                .order_by(self.db.Dataset.timestamp)
            ):
                yield timestamp, pickle.loads(data)

    def dataset_last_data(self, name):
        """This method returns the last recorded dataset under the specified name.

        :param name: name of the dataset to retrieve
        :type name: str
        :return: dataset value
        :rtype: object
        """
        with self.Session() as session:
            r = (
                session.query(self.db.Dataset)
                .filter_by(name=name)
                .order_by(self.db.Dataset.timestamp.desc())
                .first()
            )
            if r is not None:
                return r.timestamp, pickle.loads(r.data)
        return None, None

    def dataset_times(self, name):
        """This method returns the timestamp of the recorded dataset under the specified
        name.

        :param name: name of the dataset to retrieve
        :type name: str
        :return: array of timestamps
        :rtype: :class:`numpy.ndarray`
        """
        with self.Session() as session:
            t = np.array(
                [
                    timestamp
                    for timestamp, in session.query(self.db.Dataset.timestamp)
                    .filter_by(name=name)
                    .order_by(self.db.Dataset.timestamp)
                ]
            )
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

        with self.Session() as session:
            q = session.query(self.db.Dataset).filter_by(name=name)
            if ts is not None:
                q = q.filter_by(timestamp=ts)
            q = q.order_by(self.db.Dataset.timestamp)
            rows = q.all()
            if n is None:
                data = pickle.loads(rows[-1].data)
            else:
                data = pickle.loads(rows[n].data)
        return data

    def save_metadata(self, *args, **kwargs):
        """This method saves a text parameter into the database."""
        if self.readonly:
            raise RuntimeError("Cannot save metadata on readonly session")
        if not hasattr(self.db, "Metadata"):
            raise RuntimeError(
                "Metadata not supported in currently opened database (version mismatch)."
            )
        data = dict()
        for a in args:
            data.update(a)
        data.update(kwargs)
        with self.Session() as session:
            for key, val in data.items():
                r = session.query(self.db.Metadata).filter_by(name=key).one_or_none()
                if r is not None:
                    r.value = val
                else:
                    session.add(
                        self.db.Metadata(
                            name=key,
                            value=val,
                        )
                    )
            session.commit()

    def save_parameter(self, *args, **kwargs):
        """This method saves a scalar parameter into the database. Unlike scalar values
        saved by the :meth:`pymanip.asyncsession.AsyncSession.add_entry` method, such parameter
        can only hold one value, and does not have an associated timestamp.
        Parameters can be passed as dictionnaries, or keyword arguments.

        :param \\*args: dictionnaries with name-value to be added in the database
        :type \\*args: dict, optional
        :param \\**kwargs: name-value to be added in the database
        :type \\**kwargs: float, optional
        """
        if self.readonly:
            raise RuntimeError("Cannot save parameter on readonly session")
        data = dict()
        for a in args:
            data.update(a)
        data.update(kwargs)
        with self.Session() as session:
            for key, val in data.items():
                r = session.query(self.db.Parameter).filter_by(name=key).one_or_none()
                if r is not None:
                    r.value = val
                else:
                    session.add(
                        self.db.Parameter(
                            name=key,
                            value=val,
                        )
                    )
            session.commit()

    def metadata(self, name):
        """This method retrives the value of the specified metadata."""
        with self.Session() as session:
            data = session.query(self.db.Metadata).filter_by(name=name).one_or_none()
            if data is not None:
                return data.value
        return None

    def parameter(self, name):
        """This method retrieves the value of the specified parameter.

        :param name: name of the parameter to retrieve
        :type name: str
        :return: value of the parameter
        :rtype: float
        """
        with self.Session() as session:
            data = session.query(self.db.Parameter).filter_by(name=name).one_or_none()
            if data is not None:
                return data.value
        return None

    def has_metadata(self, name):
        """This method returns True if the specified metadata exists in the session database."""
        return self.metadata(name) is not None

    def has_parameter(self, name):
        """This method returns True if specified parameter exists in the session database.

        :param name: name of the parameter to retrieve
        :type name: str
        :return: True if parameter exists, False if it does not
        :rtype: bool
        """
        return self.parameter(name) is not None

    def metadatas(self):
        """This method returns all metadata."""
        with self.Session() as session:
            return {
                name: value
                for name, value in session.query(
                    self.db.Metadata.name, self.db.Metadata.value
                )
            }

    def parameters(self):
        """This method returns all parameter name and values.

        :return: parameters
        :rtype: dict
        """
        with self.Session() as session:
            return {
                name: value
                for name, value in session.query(
                    self.db.Parameter.name, self.db.Parameter.value
                )
            }

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

            # Add MPL figure images
            for fignum, fig in enumerate(self.figure_list):
                fd, fname = tempfile.mkstemp(suffix=".png")
                with os.fdopen(fd, "wb") as f_png:
                    fig.canvas.draw_idle()
                    fig.savefig(f_png)
                async with async_open(fname, "rb") as image_file:
                    figure_data = await image_file.read()
                os.remove(fname)
                p = msg.get_payload()[1]
                p.add_related(
                    figure_data,
                    maintype="image",
                    subtype="png",
                    cid="{:d}{:}".format(fignum, datestr),
                    filename="fig{:d}-{:}.png".format(fignum, datestr),
                )

            # Add egui figures images
            if self.egui_process:
                with tempfile.TemporaryDirectory() as temp_dir:
                    for fignum in self.egui_process:
                        reader, writer = await asyncio.open_connection(
                            "127.0.0.1", 6913 + fignum
                        )
                        filename = str(
                            (Path(temp_dir) / f"figure-{fignum}.png").absolute()
                        )
                        writer.write(filename.encode())
                        await writer.drain()
                        timeout = 30
                        start = time.monotonic()

                        while (
                            (time.monotonic() - start < timeout)
                            and self.running
                            and (ok := await reader.read(100)) != b"OK"
                        ):
                            await asyncio.sleep(1)

                        if ok == b"OK":
                            # File has been generated
                            print(
                                "File has been generated as",
                                filename,
                                "for figure",
                                fignum,
                            )
                            async with async_open(filename, "rb") as image_file:
                                figure_data = await image_file.read()
                            os.remove(filename)
                            p = msg.get_payload()[1]
                            p.add_related(
                                figure_data,
                                maintype="image",
                                subtype="png",
                                cid="{:d}{:}".format(fignum, datestr),
                                filename="fig{:d}-{:}.png".format(fignum, datestr),
                            )
                        else:
                            print("Error. Got", ok)

                        writer.close()
                        await writer.wait_closed()
            else:
                print("No figures to add to email")

            try:
                if use_ssl_submission:
                    smtp_server = smtplib.SMTP_SSL(host, port, timeout=5)
                else:
                    smtp_server = smtplib.SMTP(host, port, timeout=5)
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

    async def _plot_python(
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
        saved_geom = self.metadata(param_key_window)
        if saved_geom:
            saved_geom = eval(saved_geom)
        saved_figsize = self.metadata(param_key_figsize)
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
                                try:
                                    if ylim[1] < np.max(y) or ylim[0] > np.min(y):
                                        ylim = (
                                            min((ylim[0], np.min(y))),
                                            max((ylim[1], np.max(y))),
                                        )
                                        ax.set_ylim(ylim)
                                except TypeError:
                                    pass
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
                self.save_metadata(
                    **{param_key_window: str(geom), param_key_figsize: str(figsize)}
                )
            except AttributeError:
                pass

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
        backend=None,
    ):
        """This method returns an asynchronous task which creates and regularly updates a plot for
        the specified scalar variables. Such a task should be passed to :meth:`~pymanip.aiosession.aiosession.AsyncSession.monitor` or
        :meth:`~pymanip.aiosession.aiosession.AsyncSession.run`, and does not have to be awaited manually.

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
        # Save figure in database
        with self.Session() as sesn:
            ff = self.db.Figure(
                maxvalues=maxvalues,
                yscale=yscale,
                ymin=fixed_ylim[0] if fixed_ylim else float("nan"),
                ymax=fixed_ylim[1] if fixed_ylim else float("nan"),
            )
            sesn.add(ff)
            sesn.flush()
            if varnames is not None:
                for var in varnames:
                    sesn.add(
                        self.db.FigureVariable(
                            fignum=(fignum := ff.fignum),
                            name=var,
                        )
                    )
            else:
                fignum = ff.fignum
            sesn.commit()

        # Start backend
        manip_path = shutil.which("manip")
        if backend is None:
            if manip_path is None:
                backend = "python"
            else:
                backend = "manip"
        if backend == "python":
            await self._plot_python(
                varnames,
                maxvalues,
                yscale,
                x=x,
                y=y,
                fixed_ylim=fixed_ylim,
                fixed_xlim=fixed_xlim,
            )
        elif backend == "manip":
            self.egui_process.add(fignum)
            proc = await asyncio.create_subprocess_exec(
                manip_path,
                "show",
                str(self.session_path),
                "-n",
                str(fignum),
                "-p",
                str(6913 + fignum),
            )
            self.egui_process_obj.add(proc)
            # Wait until process is closed, or we have to stop running
            while self.running:
                try:
                    await asyncio.wait_for(proc.wait(), timeout=1.0)
                    break
                except TimeoutError:
                    continue
            self.egui_process.remove(fignum)
            self.egui_process_obj.remove(proc)
            print(fignum, "removed from egui_process")

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

        # Clear Figure description from database
        with self.Session() as sesn:
            sesn.execute(delete(self.db.FigureVariable))
            sesn.execute(delete(self.db.Figure))
            sesn.commit()

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
