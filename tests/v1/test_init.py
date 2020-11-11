# -*- coding: utf-8 -*-

import jwplatform


def test_default_initialization():

    KEY = 'api_key'
    SECRET = 'api_secret'

    jwp_client = jwplatform.v1.Client(KEY, SECRET)

    assert jwp_client._Client__key == KEY
    assert jwp_client._Client__secret == SECRET
    assert jwp_client._scheme == 'https'
    assert jwp_client._host == 'api.jwplatform.com'
    assert jwp_client._port is None
    assert jwp_client._api_version == 'v1'
    assert jwp_client._agent is None
    assert 'User-Agent' in jwp_client._connection.headers
    assert jwp_client._connection.headers['User-Agent'] == \
        'python-jwplatform/{}'.format(jwplatform.__version__)


def test_custom_initialization():

    KEY = '_key_'
    SECRET = '_secret_'
    SCHEME = 'http'
    HOST = 'api.host.domain'
    PORT = 8080
    API_VERSION = 'v7'
    AGENT = 'test_agent'

    jwp_client = jwplatform.v1.Client(
        KEY, SECRET,
        scheme=SCHEME,
        host=HOST,
        port=PORT,
        version=API_VERSION,
        agent=AGENT)

    assert jwp_client._Client__key == KEY
    assert jwp_client._Client__secret == SECRET
    assert jwp_client._scheme == SCHEME
    assert jwp_client._host == HOST
    assert jwp_client._port == PORT
    assert jwp_client._api_version == API_VERSION
    assert jwp_client._agent == AGENT
    assert 'User-Agent' in jwp_client._connection.headers
    assert jwp_client._connection.headers['User-Agent'] == \
        'python-jwplatform/{}-{}'.format(jwplatform.__version__, AGENT)


def test_custom_initialization_empty_kwargs():

    KEY = 'api_key'
    SECRET = 'api_secret'
    SCHEME = None
    HOST = None
    PORT = None
    API_VERSION = None
    AGENT = None

    jwp_client = jwplatform.v1.Client(
        KEY, SECRET,
        scheme=SCHEME,
        host=HOST,
        port=PORT,
        version=API_VERSION,
        agent=AGENT)

    assert jwp_client._Client__key == KEY
    assert jwp_client._Client__secret == SECRET
    assert jwp_client._scheme == 'https'
    assert jwp_client._host == 'api.jwplatform.com'
    assert jwp_client._port is None
    assert jwp_client._api_version == 'v1'
    assert jwp_client._agent is None
    assert 'User-Agent' in jwp_client._connection.headers
    assert jwp_client._connection.headers['User-Agent'] == \
        'python-jwplatform/{}'.format(jwplatform.__version__)
