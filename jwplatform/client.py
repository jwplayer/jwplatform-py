# -*- coding: utf-8 -*-

from __future__ import absolute_import

import time
import random
import hashlib

import requests

from . import PY3, __version__
from .resource import Resource

if PY3:
    from urllib.parse import quote
    unicode = lambda s: str(s)
else:
    from urllib import quote


class Client(object):
    """JW Platform API client.

    An API client for the JW Platform. For the API documentation see:
    https://developer.jwplayer.com/jw-platform/reference/v1/index.html

    Args:
        key (str): API User key
        secret (str): API User secret
        scheme (str, optional): Connection scheme: 'http' or 'https'.
                                Default is 'http'.
        host (str, optional): API server host name.
                              Default is 'api.jwplatform.com'.
        port (int, optional): API server port. Default is 80.
        version (str, optional): Version of the API to use.
                                 Default is 'v1'.
        agent (str, optional): API client agent identification string.

    Examples:
        >>> jwplatform_client = jwplatform.Client('API_KEY', 'API_SECRET')
    """

    def __init__(self, key, secret, *args, **kwargs):
        self.__key = key
        self.__secret = secret

        self._scheme = kwargs.pop('scheme', 'https')
        self._host = kwargs.pop('host', 'api.jwplatform.com')
        self._port = int(kwargs.pop('port', 80))
        self._api_version = kwargs.pop('version', 'v1')
        self._agent = kwargs.pop('agent', None)

        self._connection = requests.Session()

        self._connection.headers['User-Agent'] = 'python-jwplatform/{}{}'.format(
            __version__, '-{}'.format(self._agent) if self._agent else '')

    def __getattr__(self, resource_name):
        return Resource(resource_name, self)

    def _build_request(self, path, params=None):
        """Build API request"""

        _url = '{scheme}://{host}{port}/{version}{path}'.format(
            scheme=self._scheme,
            host=self._host,
            port=':{}'.format(self._port) if self._port != 80 else '',
            version=self._api_version,
            path=path)

        if params is not None:
            _params = params.copy()
        else:
            _params = dict()

        # Add required API parameters
        _params['api_nonce'] = str(random.randint(0, 999999999)).zfill(9)
        _params['api_timestamp'] = int(time.time())
        _params['api_key'] = self.__key
        _params['api_format'] = 'json'
        _params['api_kit'] = 'py-{}{}'.format(
            __version__, '-{}'.format(self._agent) if self._agent else '')

        # Construct Signature Base String
        sbs = '&'.join(['{}={}'.format(
            quote((unicode(key).encode('utf-8')), safe='~'),
            quote((unicode(value).encode('utf-8')), safe='~')
        ) for key, value in sorted(_params.items())])

        # Add signature to the _params dict
        _params['api_signature'] = hashlib.sha1(
            '{}{}'.format(sbs, self.__secret).encode('utf-8')).hexdigest()

        return _url, _params
