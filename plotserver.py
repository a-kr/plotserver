# coding: utf-8
import os
import io
import re
import sys
import hashlib
import datetime
from functools import wraps

from flask import Flask, Response, request
app = Flask(__name__)

try:
    import plotserver_config as user_config
except ImportError:
    user_config = object()

THISDIR = os.path.abspath(os.path.dirname(__file__))
PLOTSDIR = os.path.join(THISDIR, 'plots')
DATDIR = os.path.join(PLOTSDIR, 'dat')
PNGDIR = os.path.join(PLOTSDIR, 'png')


WRITE_PREFIX = 'read'

DT_FORMAT = '%Y-%m-%d-%H:%M:%S'


for d in [PLOTSDIR, DATDIR, PNGDIR]:
    if not os.path.isdir(d):
        os.mkdir(d)


class Config(object):
    defaults = {
        'SECRET_KEY': 'no-secret-key',
        'TRUST_KEY_LEN': 16,
        'PUBLIC_PLOTS': set(),
        'STD_SIZE': (600, 200),
        'PORT': 5000,
    }

    def __getattr__(self, k):
        try:
            return getattr(user_config, k)
        except AttributeError:
            return self.defaults[k]

config = Config()


def valid_plot_name(plot_name):
    if not re.match('[a-zA-Z0-9\-_]+', plot_name):
        return False
    return True


def gen_trust_key(plot_name, prefix=''):
    s = prefix + config.SECRET_KEY + plot_name + config.SECRET_KEY
    return hashlib.md5(s).hexdigest()[:config.TRUST_KEY_LEN]


def check_trust_key(prefix=''):
    def decorator(f):
        @wraps(f)
        def decorated(plotname, *args, **kwargs):
            if not valid_plot_name(plotname):
                return 'Invalid plot name'
            trustkey = request.args.get('trustkey')
            if not plotname in config.PUBLIC_PLOTS:
                if not trustkey or trustkey != gen_trust_key(plotname, prefix):
                    return 'Invalid trust key'
            return f(plotname, *args, **kwargs)
        return decorated
    return decorator


def make_graph(source_filename, size, result_filename, range_from=None, range_to=None):
    gnuplot = os.popen('gnuplot', 'w')
    gnuplot.write('set terminal png size %s,%s\n' % size)
    gnuplot.write('set xdata time\n')
    gnuplot.write('set timefmt "%s"\n' % DT_FORMAT)
    gnuplot.write('set output "%s"\n' % result_filename)
    gnuplot.write('set grid\n')
    gnuplot.write('unset key\n')
    gnuplot.write('plot "%s" using 1:2 index 0 with lines\n' % source_filename)
    gnuplot.close()


def load_graph(plot, size, range_from=None, range_to=None):
    w, h = size
    key = '-'
    png_filename = os.path.join(PNGDIR, '%s.%sx%s.%s.png' % (plot, w, h, key))
    dat_filename = os.path.join(DATDIR, '%s.txt' % plot)
    if not os.path.isfile(png_filename):
        make_graph(dat_filename, size, png_filename)
    data = open(png_filename, 'rb').read()
    return Response(data, mimetype='image/png')


def clean_pngs(plot):
    mask = os.path.join(PNGDIR, '%s.*.png' % plot)
    os.popen('rm ' + mask)


def push_value(plot, val):
    dat_filename = os.path.join(DATDIR, '%s.txt' % plot)
    line = datetime.datetime.now().strftime(DT_FORMAT) + ' ' + str(val) + '\n'
    with io.open(dat_filename, 'ab+') as dat:
        dat.write(line)
    clean_pngs(plot)


@app.route('/')
def index():
    return 'Hello there'


@app.route('/favicon.ico')
def favicon():
    data = open(os.path.join(THISDIR, 'favicon.ico')).read()
    return data


@app.route('/<plotname>/graph.png')
@check_trust_key()
def graph_png(plotname):
    return load_graph(plotname, config.STD_SIZE)


@app.route('/<plotname>/graph-<int:w>x<int:h>.png')
@check_trust_key()
def graph_png_sized(plotname, w, h):
    w = int(w)
    h = int(h)
    return load_graph(plotname, (w, h))


@app.route('/<plotname>/push')
@check_trust_key(prefix=WRITE_PREFIX)
def pushvalue(plotname):
    val = request.args.get('v')
    if val is None:
        return "Specify value with '?v=X'"
    push_value(plotname, val)
    return 'ok'


if __name__ == '__main__':
    if 'get-trust-key' in sys.argv:
        print 'Write key:', gen_trust_key(sys.argv[2], prefix=WRITE_PREFIX)
        print 'Read key: ', gen_trust_key(sys.argv[2])
        exit()
    app.run(debug=True, host='0.0.0.0', port=config.PORT)
