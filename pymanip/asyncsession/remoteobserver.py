"""Remote observer (:mod:`pymanip.asyncsession.remoteobserver`)
===============================================================

This module defines the :class:`~pymanip.asyncsession.RemoteObserver` class used to
access a async session live data from a remote computer.

.. autoclass:: RemoteObserver
   :members:
   :private-members:


"""

import requests
import json
from pprint import pprint


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
