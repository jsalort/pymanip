"""Read-only access to asynchronous session (:mod:`pymanip.asyncsession.savedasyncsession`)
===========================================================================================

This module defines a class for read-only access to previous session,
:class:`~pymanip.asyncsession.SavedAsyncSession`.

.. autoclass:: SavedAsyncSession
   :members:
   :private-members:

"""

from functools import lru_cache

try:
    from functools import cached_property
except ImportError:
    from backports.cached_property import cached_property
import time

import numpy as np

from fluiddyn.util.terminal_colors import cprint

from pymanip.asyncsession.asyncsession import AsyncSession
from pymanip.mytime import dateformat


class _SavedAsyncSession:
    """This class implements the same methods as AsyncSession with readonly mode, but with
    caching enabled. Also, the file is opened on demand. No context manager is necessary.
    """

    def __init__(self, session_name, verbose=True):

        self.session_name = session_name
        self.verbose = verbose
        self.session = AsyncSession(session_name, verbose=False, readonly=True)
        if verbose:
            self.print_welcome()

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
            figures = self.figures()
            if figures:
                print("Figures")
                print("=======")
                for f in figures:
                    print(f"Fig {f['fignum']}:", ",".join(f["variables"]))

    # General attributes

    @lru_cache(maxsize=128)
    def get_version(self):
        with self.session as sesn:
            return sesn.get_version()

    @cached_property
    def t0(self):
        with self.session as sesn:
            return sesn.t0

    @cached_property
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

    # Figures

    @lru_cache
    def figures(self):
        with self.session as sesn:
            return list(sesn.figures())

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
            dt = sesn.dataset_times(name)
        return dt

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

    # Metadatas

    @lru_cache(maxsize=128)
    def metadatas(self):
        if self.get_version() >= 4:
            with self.session as sesn:
                return sesn.metadatas()
        else:
            return dict()

    def metadata(self, name):
        return self.metadatas()[name]

    def has_metadata(self, name):
        return name in self.metadatas()


@lru_cache(maxsize=128)
def SavedAsyncSession(session_name, verbose=True):
    return _SavedAsyncSession(session_name, verbose=verbose)
