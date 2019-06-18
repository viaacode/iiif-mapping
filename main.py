from csv import reader
from os import getenv


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
except FileNotFoundError:
    print("File not found!")
    mappings = {}

prefix = getenv("IIIF_PREFIX_URL", "https://images.hetarchief.be/iipsrv/?IIIF=/media/5")


def app(environ, start_response):
    try:
        pid, postfix = environ['RAW_URI'].lstrip('/').split('/', 1)
        mid = mappings[pid]
    except (KeyError, ValueError):
        start_response('444 No Response', [])
        return iter([])

    url = [prefix, mid[0], mid, pid, postfix]
    url = '/'.join(url)
    response_headers = [
        ('Content-type', 'text/plain'),
        ('Content-Length', str(len(url)))
    ]
    start_response('200 OK', response_headers)
    return iter([bytes(url, 'utf-8')])
