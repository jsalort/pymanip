# -*- coding: utf-8 -*-
"""

This modules contains very simple functions for handling dates and times.
In particular, this is useful to read fluidlab's session timestamps which
are roughly in RFC 3339 format.

"""

from __future__ import unicode_literals, print_function, division
import dateutil.parser
from dateutil.tz import tzutc, tzlocal
import datetime
from time import time

def datestr2epoch(string):
    """
    Convert datestr into epoch.
    Correct string is:
    '2016-02-25T17:36+0100' or '2016-02-25T17:36+01:00'
    UTC+1 or UTC+0100 is also accepted by this function
    """
    string = string.upper()
    # Ci-dessous, on remplace UTC+1, UTC+01, UTC+0100 par +0100
    if 'UTC' in string:
        parts = string.split('UTC')
        offset = parts[1].replace(':','')
        if len(offset) == 0:
            offset = '+0000'
        elif int(offset) <= 12:
            offset = '{:+03d}00'.format(int(offset))
        string = parts[0] + offset
        #print('New string: ', string)
    date = dateutil.parser.parse(string)
    if not date.tzinfo:
        raise TypeError("datestr with no timezone information is ambiguous !")
    return (date - datetime.datetime(1970, 1, 1, tzinfo=tzutc())).total_seconds()

def epoch2datestr(epoch, tz=None):
    """
    Convert epoch into datestr.
    If no tz is given, the output is given in Coordinated Universal Time
    """
    if not tz:
        #print("Swiching to UTC")
        tz = tzutc()
    date = datetime.datetime.fromtimestamp(epoch, tz=tz)
    return date.isoformat()


if __name__ == '__main__':
    now = time()
    print("Now in local TZ:", epoch2datestr(now, tz=tzlocal()))
    print("Now in UTC:", epoch2datestr(now))
    reference = datestr2epoch('2016-02-25T17:36UTC')
    for datestr in ['2016-02-25T17:36UTC', '2016-02-25T18:36UTC+1', '2016-02-25T18:36UTC+01', '2016-02-25T18:36UTC+0100', '2016-02-25T19:36UTC+02:00', '2016-02-25T18:36+0100', '2016-02-25T17:36+0000']:
        epoch = datestr2epoch(datestr)
        datestr2 = epoch2datestr(epoch)
        epoch2 = datestr2epoch(datestr2)
        if epoch == epoch2 and epoch == reference:
            print("{:s} {:}".format(datestr, epoch))
