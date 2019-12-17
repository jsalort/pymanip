"""Time utilities (:mod:`pymanip.mytime`)
=========================================

This modules contains very simple functions for handling dates and times.
In particular, the :func:`datestr2epoch` is useful to read fluidlab's session timestamps
which are roughly in RFC 3339 format.

.. autofunction:: sleep

.. autofunction:: datestr2epoch

.. autofunction:: epoch2datestr

.. autofunction:: tic

.. autofunction:: toc

"""

import datetime
from time import time
import sys
import warnings
from platform import platform
import dateutil.parser
from dateutil.tz import tzutc, tzlocal
import matplotlib.pyplot as plt
import six

if platform().startswith("Windows"):
    dateformat = "%A %d %B %Y - %X (%z)"
else:
    dateformat = "%A %e %B %Y - %H:%M:%S (UTC%z)"


def sleep(duration):
    """Prints a timer for specified duration.
    This is mostly similar to :meth:`pymanip.asyncsession.AsyncSession.sleep`, except that
    it is meant to be used outside a session.

    :param duration: the duration for which to sleep
    :type duration: float
    """
    debut = time()
    while (time() - debut) < duration:
        if six.PY2:
            sys.stdout.write(
                (
                    "Sleeping for "
                    + str(-int(time() - debut - duration))
                    + " s"
                    + " " * 35
                    + "\r"
                ).encode("utf-8")
            )
        else:
            sys.stdout.write(
                (
                    "Sleeping for "
                    + str(-int(time() - debut - duration))
                    + " s"
                    + " " * 35
                    + "\r"
                )
            )
        sys.stdout.flush()
        # time.sleep(1.0)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            plt.pause(1.0)
    sys.stdout.write("\n")


def datestr2epoch(string):
    """Convert datestr into epoch.
    Correct string is:
    '2016-02-25T17:36+0100' or '2016-02-25T17:36+01:00'.

    UTC+1 or UTC+0100 is also accepted by this function
    Accepts a single string or a list of string
    """
    if isinstance(string, str):
        string = string.upper()
        # Ci-dessous, on remplace UTC+1, UTC+01, UTC+0100 par +0100
        if "UTC" in string:
            parts = string.split("UTC")
            offset = parts[1].replace(":", "")
        if len(offset) == 0:
            offset = "+0000"
        elif int(offset) <= 12:
            offset = "{:+03d}00".format(int(offset))
        string = parts[0] + offset
        # print('New string: ', string)
        date = dateutil.parser.parse(string)
        if not date.tzinfo:
            raise TypeError("datestr with no timezone information " "is ambiguous !")
        return (date - datetime.datetime(1970, 1, 1, tzinfo=tzutc())).total_seconds()
    else:
        dlist = []
        for s in string:
            s = s.upper()
            # Ci-dessous, on remplace UTC+1, UTC+01, UTC+0100 par +0100
            if "UTC" in s:
                parts = s.split("UTC")
                offset = parts[1].replace(":", "")
            if len(offset) == 0:
                offset = "+0000"
            elif int(offset) <= 12:
                offset = "{:+03d}00".format(int(offset))
            s = parts[0] + offset
            # print('New string: ', string)
            date = dateutil.parser.parse(s)
            if not date.tzinfo:
                raise TypeError(
                    "datestr with no timezone information " "is ambiguous !"
                )
            dlist.append(
                (date - datetime.datetime(1970, 1, 1, tzinfo=tzutc())).total_seconds()
            )
        return dlist


def epoch2datestr(epoch, tz=None):
    """Convert epoch into datestr.
    If no tz is given, the output is given in Coordinated Universal Time
    """
    if not tz:
        # print("Swiching to UTC")
        tz = tzutc()
    date = datetime.datetime.fromtimestamp(epoch, tz=tz)
    return date.isoformat()


tic_starts = []


def tic():
    """Simple timer start.
    """
    tic_starts.append(time())


def toc(comment=None):
    """Simpler timer stop.

    :param comment: comment for print
    :type comment: str, optional
    """
    if comment is None:
        print("Elapsed time {:.2f} seconds.".format(time() - tic_starts[-1]))
    else:
        print(comment, "{:.2f} seconds.".format(time() - tic_starts[-1]))


if __name__ == "__main__":
    now = time()
    print("Now in local TZ:", epoch2datestr(now, tz=tzlocal()))
    print("Now in UTC:", epoch2datestr(now))
    reference = datestr2epoch("2016-02-25T17:36UTC")
    for datestr in [
        "2016-02-25T17:36UTC",
        "2016-02-25T18:36UTC+1",
        "2016-02-25T18:36UTC+01",
        "2016-02-25T18:36UTC+0100",
        "2016-02-25T19:36UTC+02:00",
        "2016-02-25T18:36+0100",
        "2016-02-25T17:36+0000",
    ]:
        epoch = datestr2epoch(datestr)
        datestr2 = epoch2datestr(epoch)
        epoch2 = datestr2epoch(datestr2)
        if epoch == epoch2 and epoch == reference:
            print("{:s} {:}".format(datestr, epoch))
