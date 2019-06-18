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
    empty_response = iter([])

    if mappings is None:
        start_response('503 Service Unavailable', [])
        return empty_response

    if environ['RAW_URI'] == '/':
        start_response('200 OK', [])
        return empty_response

    try:
        pid, postfix = environ['RAW_URI'].lstrip('/').split('/', 1)
        mid = mappings[pid]
    except (KeyError, ValueError):
        start_response('404 Not Found', [])
        return empty_response

    url = [prefix, mid[0], mid, pid, postfix]
    url = '/'.join(url)
    response_headers = [
        ('Content-type', 'text/plain'),
        ('Content-Length', '0'),
        ('X-Accel-Redirect', url),
    ]
    start_response('200 OK', response_headers)
    return empty_response
