# -*- coding: utf-8 -*-

import time
import random
import hashlib
from urllib.parse import quote
from typing import Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from jwplatform import __version__
from jwplatform.v1.resource import Resource

BACKOFF_FACTOR = 1.7
RETRY_COUNT = 5


class RetryAdapter(HTTPAdapter):
    """Exponential backoff http adapter."""
    def __init__(self, *args, **kwargs):
        super(RetryAdapter, self).__init__(*args, **kwargs)
        self.max_retries = Retry(total=RETRY_COUNT,
                                 backoff_factor=BACKOFF_FACTOR)


class Client:
    """JW Platform API client.

    An API client for the JW Platform. For the API documentation see:
    https://developer.jwplayer.com/jw-platform/reference/v1/index.html

    Args:
        key (str): API User key
        secret (str): API User secret
        scheme (str, optional): Connection scheme: 'http' or 'https'.
                                Default is 'https'.
        host (str, optional): API server host name.
                              Default is 'api.jwplatform.com'.
        port (int, optional): API server port. Default is 443.
        version (str, optional): Version of the API to use.
                                 Default is 'v1'.
        agent (str, optional): API client agent identification string.

    Examples:
        >>> jwplatform_client = jwplatform.Client('API_KEY', 'API_SECRET')
    """

    def __init__(self, key: str, secret: str, *args, **kwargs):
        self.__key = key
        self.__secret = secret

        self._scheme = kwargs.get('scheme') or 'https'
        self._host = kwargs.get('host') or 'api.jwplatform.com'
        self._port = int(kwargs['port']) if kwargs.get('port') else None
        self._api_version = kwargs.get('version') or 'v1'
        self._agent = kwargs.get('agent')

        self._connection = requests.Session()
        self._connection.mount(self._scheme, RetryAdapter())

        self._connection.headers['User-Agent'] = 'python-jwplatform/{}{}'.format(
            __version__, '-{}'.format(self._agent) if self._agent else '')

    def __getattr__(self, resource_name):
        return Resource(resource_name, self)

    def _build_request(self, path: str, params: Optional[Dict] = None):
        """Build API request."""

        _url = '{scheme}://{host}{port}/{version}{path}'.format(
            scheme=self._scheme,
            host=self._host,
            port=':{}'.format(self._port) if self._port else '',
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

        # Collect params to a list
        # The reason using a list instead of a dict is
        # to allow the same key multiple times with the different values in the query string
        params_for_sbs = list()
        for key, value in sorted(_params.items()):
            key = quote(str(key).encode('utf-8'), safe='~')
            if isinstance(value, list):
               for item in value:
                   item = quote(str(item).encode('utf-8'), safe='~')
                   params_for_sbs.append(f"{key}={item}")
            else:
                value = quote(str(value).encode('utf-8'), safe='~')
                params_for_sbs.append(f"{key}={value}")

        # Construct Signature Base String
        sbs = "&".join(params_for_sbs)

        # Add signature to the _params dict
        _params['api_signature'] = hashlib.sha1(
            '{}{}'.format(sbs, self.__secret).encode('utf-8')).hexdigest()

        return _url, _params
