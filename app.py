from csv import reader
from os import getenv
import logging
import requests
import re
from lump.http import dbus_connect
from lxml import objectify
from collections import namedtuple
from urllib.parse import urlparse
import json

logger = logging.getLogger()

Item = namedtuple('Item', ['pid', 'mediafile_id', 'asset_id', 'image_path'])
mediamosa_config = {
    "host": getenv('MEDIAMOSA_HOST'),
    "user": getenv('MEDIAMOSA_USER'),
    "password": getenv('MEDIAMOSA_PASS')
}


class Mappings:
    is_checked = set()

    def __init__(self, csv_file):
        mappings_ = dict()
        with open(csv_file) as f:
            csv = reader(f)
            header = next(csv)
            idx_pid = header.index('pid')
            idx_mediafile_id = header.index('mediafile_id')
            idx_asset_id = header.index('asset_id')
            for line in csv:
                mappings_[line[idx_pid]] = Item(
                    line[idx_pid],
                    line[idx_mediafile_id],
                    line[idx_asset_id],
                    None
                )
        self.mappings = mappings_

    def _assure_iiif_available(self, item):
        conn = dbus_connect(**mediamosa_config)

        url = mediamosa_config['host']
        url += '/asset/%s/play?user_id=%s&mediafile_id=%s&autostart=true&count_play=true'
        url %= (item.asset_id, 'iiif', item.mediafile_id)

        image = objectify.fromstring(conn.get(url).content)
        image = str(image['items']['item']['output'])
        image = urlparse(image).path
        item = item._replace(image_path=image)
        self.mappings[item.pid] = item
        return item

    def __getitem__(self, key):
        item = self.mappings[key]
        if item.image_path is not None:
            return item
        return self._assure_iiif_available(item)


try:
    mappings = Mappings(getenv('IIIF_MAPPING_FILE', 'mappings.csv'))
except FileNotFoundError as e:
    logging.getLogger().exception(e)
    mappings = None

prefix = getenv("IIIF_PREFIX_URI", "/iipsrv/?IIIF=")
prefix_host = getenv('IIIF_PREFIX_HOST', "https://images.hetarchief.be")
replace_id = re.compile(r'("@id"\s*:\s*")[^"]+(")')
remove_query_string = re.compile(r'\?.*$')


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

    uri = remove_query_string.sub('', environ['RAW_URI'])
    if uri == '/':
        return '200 OK'

    parts = uri.lstrip('/').split('/', 1)
    pid = parts.pop(0)
    try:
        item = mappings[pid]
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

    url = [prefix + item.image_path, postfix]
    url = '/'.join(url)

    if postfix != 'info.json':
        logging.getLogger().info(url)
        return '200 OK', [
            ('X-Accel-Redirect', url),
        ]

    is_https = getenv('IS_HTTPS', False)
    new_url = environ['HTTP_HOST']
    if is_https:
        new_url = 'https://' + new_url
    else:
        new_url = 'http://' + new_url
    new_url += '/' + pid
    contents = requests.get(prefix_host + url).content.decode('UTF-8')
    contents = replace_id.sub(r'\1' + new_url + r'\2', contents)

    contents = json.loads(contents)
    contents["rights"] = getenv("RIGHTS_URL")
    contents = json.dumps(contents)

    return '200 OK', [
        ('Content-Type', 'application/json'),
        ('Access-Control-Allow-Origin', '*'),
    ], bytes(contents, encoding='UTF-8')
