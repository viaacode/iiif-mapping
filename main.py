from csv import reader
from os import getenv
import logging

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
    status, headers = response(environ)
    headers.append(('Content-Length', '0'))
    start_response(status, headers)
    return iter([])


def response(environ):
    if mappings is None:
        return '503 Service Unavailable', []

    uri = environ['RAW_URI']
    if uri == '/':
        return '200 OK', []

    parts = uri.lstrip('/').split('/', 1)
    pid = parts.pop(0)
    try:
        mid = mappings[pid]
    except KeyError:
        return '404 Not Found', []

    if not len(parts) or parts[0] == '':
        # by default redirect to the info.json file
        return '303 See Other', [
            ('Location', '/%s/info.json' % (pid,)),
        ]

    url = [prefix, mid[0], mid, pid, parts[0]]
    url = '/'.join(url)

    return '200 OK', [
        ('X-Accel-Redirect', url),
    ]
