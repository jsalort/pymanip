"""

This module defines another kind of session, meant to be used for asynchronous
monitoring, where each variable can be logged with its own timestamp.

"""

import signal
import time
import sys
import os.path
import pickle
import warnings

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
from clint.textui import colored

try:
    import PyQt5.QtCore
except ModuleNotFoundError:
    pass

from pymanip.mytime import dateformat

__all__ = ['AsyncSession']


class AsyncSession:
    database_version = 3

    def __init__(self, session_name=None, variable_list=None, verbose=True):
        if variable_list is None:
            variable_list = []
        self.session_name = session_name
        if session_name is None:
            self.conn = sqlite3.connect(':memory:')
        else:
            self.conn = sqlite3.connect(session_name + '.db')
        with self.conn as c:
            tables = list(c.execute("SELECT name FROM sqlite_master;"))
            if not tables:
                c.execute("""
                    CREATE TABLE log_names (
                    name TEXT);
                    """)
                c.execute("""
                    CREATE TABLE log (
                    timestamp INT,
                    name TEXT,
                    value REAL);
                    """)
                c.execute("""
                    CREATE TABLE dataset_names (
                    name TEXT);
                    """)
                c.execute("""
                    CREATE TABLE dataset (
                    timestamp INT,
                    name TEXT,
                    data BLOB);
                    """)
                c.execute("""
                    CREATE TABLE parameters (
                        name TEXT,
                        value REAL);
                    """)
                c.execute("""
                    INSERT INTO parameters
                    (name, value)
                    VALUES (?,?);
                    """, ('_database_version', AsyncSession.database_version))
                c.execute("""
                    INSERT INTO parameters
                    (name, value)
                    VALUES (?,?);
                    """, ('_session_creation_timestamp',
                          datetime.now().timestamp()))
            elif verbose:
                self.print_welcome()
        self.figure_list = []
        self.template_dir = os.path.join(os.path.dirname(__file__), 'web')
        self.static_dir = os.path.join(os.path.dirname(__file__), 'web_static')
        self.jinja2_loader = jinja2.FileSystemLoader(self.template_dir)

    def __enter__(self):
        return self

    def __exit__(self, type_, value, cb):
        self.conn.close()

    def get_version(self):
        version = self.parameter('_database_version')
        if version is None:
            version = 1
        return version

    @property
    def t0(self):
        if hasattr(self, '_session_creation_timestamp'):
            return self._session_creation_timestamp
        t0 = self.parameter('_session_creation_timestamp')
        if t0 is not None:
            self._session_creation_timestamp = t0
            return t0
        logged_data = self.logged_first_values()
        if logged_data:
            t0 = min([v[0] for k, v in logged_data.items()])
            self.save_parameter(_session_creation_timestamp=t0)
            self._session_creation_timestamp = t0
            return t0
        return 0

    @property
    def initial_timestamp(self):
        return self.t0

    @property
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

    def print_welcome(self):
        start_string = time.strftime(dateformat,
                                     time.localtime(self.initial_timestamp))
        print(colored.blue('*** Start date: ' + start_string))
        last = self.last_timestamp
        if last:
            end_string = time.strftime(dateformat,
                                       time.localtime(last))
            print(colored.blue('***   End date: ' + end_string))

    def add_entry(self, **kwargs):
        ts = datetime.now().timestamp()
        with self.conn as c:
            cursor = c.cursor()
            cursor.execute('SELECT name FROM log_names;')
            names = set([d[0] for d in cursor.fetchall()])
            for key, val in kwargs.items():
                if key not in names:
                    c.execute('INSERT INTO log_names VALUES (?);',
                              (key,))
                    names.add(key)
                c.execute('INSERT INTO log VALUES (?,?,?);',
                          (ts, key, val))

    def add_dataset(self, **kwargs):
        ts = datetime.now().timestamp()
        with self.conn as c:
            cursor = c.cursor()
            cursor.execute('SELECT name FROM dataset_names;')
            names = set([d[0] for d in cursor.fetchall()])
            for key, val in kwargs.items():
                if key not in names:
                    c.execute('INSERT INTO dataset_names VALUES (?);',
                              (key,))
                    names.add(key)
                c.execute('INSERT INTO dataset VALUES (?,?,?);',
                          (ts, key, pickle.dumps(val, protocol=4)))

    def logged_variables(self):
        with self.conn as conn:
            c = conn.cursor()
            c.execute('SELECT name FROM log_names;')
            data = c.fetchall()
        names = set([d[0] for d in data])
        return names

    def logged_data(self):
        names = self.logged_variables()
        result = dict()
        for name in names:
            result[name] = self.__getitem__(name)
        return result

    def logged_first_values(self):
        with self.conn as conn:
            c = conn.cursor()
            c.execute('SELECT name FROM log_names;')
            names = set([d[0] for d in c.fetchall()])
            result = dict()
            for name in names:
                c.execute("""SELECT timestamp, value FROM log
                             WHERE name='{:}'
                             ORDER BY timestamp ASC
                             LIMIT 1;
                          """.format(name))
                result[name] = c.fetchone()
        return result

    def logged_last_values(self):
        with self.conn as conn:
            c = conn.cursor()
            c.execute('SELECT name FROM log_names;')
            names = set([d[0] for d in c.fetchall()])
            result = dict()
            for name in names:
                c.execute("""SELECT timestamp, value FROM log
                             WHERE name='{:}'
                             ORDER BY timestamp DESC
                             LIMIT 1;
                          """.format(name))
                result[name] = c.fetchone()
        return result

    def logged_data_fromtimestamp(self, name, timestamp):
        with self.conn as conn:
            c = conn.cursor()
            c.execute("""SELECT timestamp, value FROM log
                         WHERE name='{:}' AND timestamp > {:}
                         ORDER BY timestamp ASC;
                      """.format(name, timestamp))
            data = c.fetchall()
        t = np.array([d[0] for d in data if d[1] is not None])
        v = np.array([d[1] for d in data if d[1] is not None])
        return t, v

    def dataset_names(self):
        with self.conn as conn:
            c = conn.cursor()
            try:
                c.execute("SELECT name from dataset_names;")
                data = c.fetchall()
            except sqlite3.OperationalError:
                return set()
        return set([d[0] for d in data])

    def datasets(self, name):
        with self.conn as conn:
            c = conn.cursor()
            it = c.execute("""SELECT timestamp, data FROM dataset
                              WHERE name='{:}'
                              ORDER BY timestamp ASC;
                           """.format(name))
            for row in it:
                yield row[0], pickle.loads(row[1])

    def dataset_last_data(self, name):
        return next(self.datasets(name))

    def dataset_times(self, name):
        with self.conn as conn:
            c = conn.cursor()
            it = c.execute("""SELECT timestamp FROM dataset
                              WHERE name='{:}'
                              ORDER BY timestamp ASC;
                           """.format(name))
            t = np.array([v[0] for v in it])
        return t

    def dataset(self, name, ts):
        with self.conn as conn:
            c = conn.cursor()
            c.execute("""SELECT data FROM dataset
                         WHERE name='{:}' AND timestamp='{:}';
                      """.format(name, ts))
            data = pickle.loads(c.fetchone()[0])
        return data

    def save_parameter(self, **kwargs):
        with self.conn as conn:
            c = conn.cursor()
            for key, val in kwargs.items():
                c.execute("""SELECT rowid FROM parameters
                             WHERE name='{:}';
                          """.format(key))
                rowid = c.fetchone()
                if rowid is not None:
                    rowid = rowid[0]
                    c.execute("""
                        REPLACE INTO parameters
                        (rowid, name, value)
                        VALUES (?,?,?);
                        """, (rowid, key, val))
                else:
                    c.execute("""
                        INSERT INTO parameters
                        (name, value)
                        VALUES (?,?);
                        """, (key, val))

    def parameter(self, name):
        with self.conn as conn:
            c = conn.cursor()
            c.execute("""
                      SELECT value FROM parameters
                      WHERE name='{:}';
                      """.format(name))
            data = c.fetchone()
            if data:
                return data[0]
        return None

    def has_parameter(self, name):
        return self.parameter(name) is not None

    def parameters(self):
        with self.conn as conn:
            c = conn.cursor()
            c.execute('SELECT * FROM parameters;')
            data = c.fetchall()
        return {d[0]: d[1] for d in data}

    def __getitem__(self, key):
        with self.conn as conn:
            c = conn.cursor()
            c.execute("""
                      SELECT timestamp, value FROM log
                      WHERE name='{:}';
                      """.format(key))
            data = c.fetchall()
        t = np.array([d[0] for d in data])
        v = np.array([d[1] for d in data])
        return t, v

    async def send_email(self, from_addr, to_addrs, host, port=25,
                         subject=None, delay_hours=6,
                         initial_delay_hours=None):
        """
        Asynchronous task which sends an email every delay_hours hours.
        """

        if self.session_name is None:
            title = "Pymanip session"
        else:
            title = self.session_name
        if subject is None:
            subject = title

        if initial_delay_hours is None:
            initial_delay_hours = delay_hours/2

        if initial_delay_hours > 0:
            await self.sleep(initial_delay_hours*3600, verbose=False)

        jinja2_autoescape = jinja2.select_autoescape(['html'])
        jinja2_env = jinja2.Environment(loader=self.jinja2_loader,
                                        autoescape=jinja2_autoescape)
        template = jinja2_env.get_template("email.html")

        while self.running:

            dt_n = datetime.now()
            dt_fmt = '{:}{:02d}{:02d}-{:02d}{:02d}{:02d}'
            datestr = dt_fmt.format(dt_n.year, dt_n.month,
                                    dt_n.day, dt_n.hour,
                                    dt_n.minute, dt_n.second)
            # Generate HTML content
            last_values = self.logged_last_values()
            for name in last_values:
                timestamp, value = last_values[name]
                last_values[name] = (timestamp, value,
                                     time.strftime(dateformat,
                                                   time.localtime(timestamp)))
            n_figs = len(self.figure_list)
            message_html = template.render(title=title,
                                           fignums=range(n_figs),
                                           datestr=datestr,
                                           last_values=last_values)

            # Create Email message
            msg = EmailMessage()
            msg['Subject'] = subject
            msg['From'] = from_addr
            msg['To'] = to_addrs
            msg.set_content("This is a MIME message")
            msg.add_alternative(message_html, subtype='html')

            # Add figure images
            for fignum, fig in enumerate(self.figure_list):
                fd, fname = tempfile.mkstemp(suffix=".png")
                with os.fdopen(fd, 'wb') as f_png:
                    fig.canvas.draw_idle()
                    fig.savefig(f_png)
                with open(fname, 'rb') as image_file:
                    figure_data = image_file.read()
                os.remove(fname)
                p = msg.get_payload()[1]
                p.add_related(figure_data,
                              maintype='image',
                              subtype='png',
                              cid='{:d}{:}'.format(fignum, datestr),
                              filename='fig{:d}-{:}.png'.format(fignum,
                                                                datestr))

            with smtplib.SMTP(host, port) as smtp:
                try:
                    smtp.send_message(msg)
                    print("Email sent!")
                except smtplib.SMTPHeloError:
                    print('SMTP Helo Error')
                except smtplib.SMTPRecipientsRefused:
                    print('Some recipients have been rejected by SMTP server')
                except smtplib.SMTPSenderRefused:
                    print('SMTP server refused sender ' + self.email_from_addr)
                except smtplib.SMTPDataError:
                    print('SMTP Data Error')

            await self.sleep(delay_hours*3600, verbose=False)

    async def plot(self, varnames, maxvalues=1000, yscale=None):
        if isinstance(varnames, str):
            varnames = (varnames,)
        param_key_window = '_window_' + '_'.join(varnames)
        param_key_figsize = '_figsize_' + '_'.join(varnames)
        last_update = {k: 0 for k in varnames}
        saved_geom = self.parameter(param_key_window)
        if saved_geom:
            saved_geom = eval(saved_geom)
        saved_figsize = self.parameter(param_key_figsize)
        if saved_figsize:
            saved_figsize = eval(saved_figsize)
        plt.ion()
        fig = plt.figure(figsize=saved_figsize)
        mngr = fig.canvas.manager
        if saved_geom:
            mngr.window.setGeometry(saved_geom)
        ax = fig.add_subplot(111)
        line_objects = dict()
        self.figure_list.append(fig)
        ts0 = self.initial_timestamp
        while self.running:
            data = {k: self.logged_data_fromtimestamp(k, last_update[k])
                    for k in varnames}
            for name, values in data.items():
                ts, vs = values
                if ts.size > 0:
                    if name in line_objects:
                        #print('updating plot')
                        p = line_objects[name]
                        x = np.hstack((p.get_xdata(), (ts-ts0)/3600))
                        y = np.hstack((p.get_ydata(), vs))
                        if x.size > maxvalues:
                            x = x[-maxvalues:]
                            y = y[-maxvalues:]
                        p.set_xdata(x)
                        p.set_ydata(y)
                        ylim = ax.get_ylim()
                        if x[0] != x[-1]:
                            ax.set_xlim((x[0], x[-1]))
                        if ylim[1] < np.max(y) or ylim[0] > np.min(y):
                            ylim = (min((ylim[0], np.min(y))),
                                    max((ylim[1], np.max(y))))
                            ax.set_ylim(ylim)
                    else:
                        #print('initial plot')
                        x = (ts-ts0)/3600
                        y = vs
                        if x.size > maxvalues:
                            x = x[-maxvalues:]
                            y = y[-maxvalues:]
                        p, = ax.plot(x, y, 'o-', label=name)
                        line_objects[name] = p
                        ax.set_xlabel('t [h]')
                        if x[0] != x[-1]:
                            ax.set_xlim((x[0], x[-1]))
                        if yscale:
                            ax.set_yscale(yscale)
                        ax.legend()
                        fig.show()
                    last_update[name] = ts[-1]
            await asyncio.sleep(1)

        # Saving figure positions
        try:
            geom = mngr.window.geometry()
            figsize = tuple(fig.get_size_inches())
            self.save_parameter(**{param_key_window: str(geom),
                                   param_key_figsize: str(figsize)})
        except AttributeError:
            pass

    async def figure_gui_update(self):
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore",
                                    category=MatplotlibDeprecationWarning)
            while self.running:
                if self.figure_list:
                    for fig in self.figure_list:
                        fig.canvas.start_event_loop(0.7/len(self.figure_list))
                        await asyncio.sleep(0.3/len(self.figure_list))
                    await asyncio.sleep(0.05)
                else:
                    await asyncio.sleep(1.0)

    def ask_exit(self, *args, **kwargs):
        self.running = False
        print(' Signal caught... stopping...')

    async def sleep(self, duration, verbose=True):
        start = time.monotonic()
        while self.running and time.monotonic()-start < duration:
            if verbose:
                print("Sleeping for " +
                      str(-int(time.monotonic()-start-duration)) +
                      " s" + " "*8, end='\r')
                sys.stdout.flush()
            await asyncio.sleep(0.5)
        if verbose:
            sys.stdout.write("\n")

    async def server_main_page(self, request):
        print('[', datetime.now(), request.remote, request.rel_url, ']')
        if self.session_name:
            context = {'title': self.session_name}
        else:
            context = {'title': 'pymanip'}
        response = aiohttp_jinja2.render_template('main.html',
                                                  request,
                                                  context)
        return response

    async def server_logged_last_values(self, request):
        #print('[', datetime.now(), request.remote, request.rel_url, ']')
        data = [{'name': name,
                 'value': v[1],
                 'datestr': time.strftime(dateformat, time.localtime(v[0]))}
                for name, v in self.logged_last_values().items()]
        return web.json_response(data)

    async def server_plot_page(self, request):
        print('[', datetime.now(), request.remote, request.rel_url, ']')
        context = {'name': request.match_info['name']}
        response = aiohttp_jinja2.render_template('plot.html',
                                                  request,
                                                  context)
        return response

    async def server_data_from_ts(self, request):
        data_in = await request.json()
        last_ts = data_in['last_ts']
        name = data_in['name']
        timestamps, values = self.logged_data_fromtimestamp(name, last_ts)
        data_out = list(zip(timestamps, values))
        #print('from', last_ts, data_out)
        return web.json_response(data_out)

    async def mytask(self, corofunc):
        print('Starting task', corofunc)
        while self.running:
            await corofunc(self)
        print('Task finished', corofunc)

    def run(self, *tasks):
        loop = asyncio.get_event_loop()

        # signal handling
        self.running = True
        if sys.platform == 'win32':
            # loop.add_signal_handler raises NotImplementedError
            signal.signal(signal.SIGINT, self.ask_exit)
        else:
            for signame in ('SIGINT', 'SIGTERM'):
                loop.add_signal_handler(getattr(signal, signame),
                                        self.ask_exit)

        # web server
        app = web.Application(loop=loop)
        aiohttp_jinja2.setup(app, loader=self.jinja2_loader)
        app.router.add_routes([web.get('/',
                                       self.server_main_page),
                               web.get('/api/logged_last_values',
                                       self.server_logged_last_values),
                               web.get('/plot/{name}',
                                       self.server_plot_page),
                               web.static('/static',
                                          self.static_dir),
                               web.post('/api/data_from_ts',
                                        self.server_data_from_ts)])

        webserver = loop.create_server(app.make_handler(),
                                       host=None, port=6913)

        # if any of the tasks submitted are coroutinefunctions instead of
        # coroutines, then assume they take only one argument (self)
        tasks_final = list()
        for t in tasks:
            if asyncio.iscoroutinefunction(t):
                tasks_final.append(self.mytask(t))
            elif asyncio.iscoroutine(t):
                tasks_final.append(t)
            else:
                raise TypeError('Coroutine or Coroutinefunction is expected')
        print('Starting event loop')
        loop.run_until_complete(asyncio.gather(webserver,
                                               self.figure_gui_update(),
                                               *tasks_final))


if __name__ == '__main__':
    with AsyncSession('Essai') as sesn:
        sesn.add_entry(a=1, b=2)
        sesn.save_parameter(c=3)
        sesn.plot('a')
