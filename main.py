from csv import reader
from os import getenv
import logging
import requests

logging.basicConfig()


class Mappings:
    def __init__(self, csv_file):
        mappings_ = dict()
        with open(csv_file) as f:
            csv = reader(f)
            header = next(csv)
            idx_mid = header.index('mid')
            idx_pid = header.index('pid')
            for line in csv:
                mappings_[line[idx_pid]] = line[idx_mid]
        self.mappings = mappings_

    def __getitem__(self, key):
        return self.mappings[key]


try:
    mappings = Mappings(getenv('IIIF_MAPPING_FILE', 'mappings.csv'))
except FileNotFoundError as e:
    logging.getLogger().exception(e)
    mappings = None

prefix = getenv("IIIF_PREFIX_URL", "/iipsrv/?IIIF=/media/5")


def app(environ, start_response):
    resp = response(environ)
    if type(resp) is str:
        status = resp
        resp = []
    else:
        status = resp[0]

    try:
        headers = resp[1]
    except IndexError:
        headers = []

    try:
        content = resp[2]
    except IndexError:
        content = b''

    headers.append(('Content-Length', str(len(content))))
    start_response(status, headers)
    return iter([content])


def response(environ):
    if mappings is None:
        return '503 Service Unavailable'

    uri = environ['RAW_URI']
    if uri == '/':
        return '200 OK'

    parts = uri.lstrip('/').split('/', 1)
    pid = parts.pop(0)
    try:
        mid = mappings[pid]
    except KeyError:
        return '404 Not Found'

    if not len(parts) or parts[0] == '':
        # by default redirect to the info.json file
        return '303 See Other', [
            ('Location', '/%s/info.json' % (pid,)),
        ]

    try:
        postfix = parts.pop()
    except IndexError:
        postfix = ''

    url = [prefix, mid[0], mid, pid, postfix]
    url = '/'.join(url)

    is_https = environ['wsgi.url_scheme'] == 'https'

    if postfix == 'info.json' and is_https:
        contents = requests.get(url)
        print(environ)
        return '200 OK', [
            ('Content-Type', 'application/json')
        ], bytes(contents.content.replace(b'http://', b'https://'))

    return '200 OK', [
        ('X-Accel-Redirect', url),
    ]
