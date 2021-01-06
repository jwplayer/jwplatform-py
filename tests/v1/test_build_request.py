# -*- coding: utf-8 -*-

import time
import hashlib
import jwplatform

from urllib.parse import quote


def test_required_parameters_present():

    KEY = 'api_key'
    SECRET = 'api_secret'

    jwp_client = jwplatform.v1.Client(KEY, SECRET)

    url, params = jwp_client._build_request('')

    assert url == 'https://api.jwplatform.com/v1'

    assert 'api_nonce' in params
    assert len(params['api_nonce']) == 9
    assert 0 <= int(params['api_nonce']) <= 999999999

    assert 'api_timestamp' in params
    assert params['api_timestamp'] <= int(time.time())

    assert 'api_key' in params
    assert params['api_key'] == KEY

    assert 'api_format' in params
    assert params['api_format'] == 'json'

    assert 'api_kit' in params
    assert params['api_kit'] == 'py-{}'.format(jwplatform.__version__)

    assert 'api_signature' in params


def test_request_url():

    KEY = '_key_'
    SECRET = '_secret_'
    SCHEME = 'http'
    HOST = 'api.host.domain'
    PORT = 8080
    API_VERSION = 'v3'
    AGENT = 'test_request_url'
    PATH = '/a/b/c/d'

    jwp_client = jwplatform.v1.Client(
        KEY, SECRET,
        scheme=SCHEME,
        host=HOST,
        port=PORT,
        version=API_VERSION,
        agent=AGENT)

    url, params = jwp_client._build_request(PATH)

    assert url == '{scheme}://{host}:{port}/{version}{path}'.format(
        scheme=SCHEME,
        host=HOST,
        port=PORT,
        version=API_VERSION,
        path=PATH)


def test_signature_none_array_values_only():

    KEY = 'api_key'
    SECRET = 'api_secret'
    PATH = '/test/resource/show'

    request_params = {
        'a': 1,
        'b': 'two',
        'c3': 'Param 3',
        u'❄': u'⛄',
        't1': True,
        'n0': None
    }

    jwp_client = jwplatform.v1.Client(KEY, SECRET)

    url, params = jwp_client._build_request(PATH, request_params)

    assert url == 'https://api.jwplatform.com/v1{}'.format(PATH)
    assert 'api_nonce' in params
    assert 'api_timestamp' in params
    assert 'api_key' in params
    assert 'api_format' in params
    assert 'api_kit' in params
    assert 'api_signature' in params

    request_params['api_nonce'] = params['api_nonce']
    request_params['api_timestamp'] = params['api_timestamp']
    request_params['api_key'] = params['api_key']
    request_params['api_format'] = params['api_format']
    request_params['api_kit'] = params['api_kit']

    base_str = '&'.join(['{}={}'.format(
        quote(str(key).encode('utf-8'), safe='~'),
        quote(str(value).encode('utf-8'), safe='~')
    ) for key, value in sorted(request_params.items())])

    assert params['api_signature'] == hashlib.sha1(
        '{}{}'.format(base_str, SECRET).encode('utf-8')).hexdigest()

def test_signature_with_array_values():

    KEY = 'api_key'
    SECRET = 'api_secret'
    PATH = '/test/resource/show'

    request_params = {
        'a': 1,
        'b': 'two',
        'c3': 'Param 3',
        u'❄': u'⛄',
        't1': True,
        'n0': None,
        'test_array1': [1, 2, 3, 4],
        'test_array2': ["test item1", "test item2"],
    }

    jwp_client = jwplatform.v1.Client(KEY, SECRET)

    url, params = jwp_client._build_request(PATH, request_params)

    assert url == 'https://api.jwplatform.com/v1{}'.format(PATH)
    assert 'api_nonce' in params
    assert 'api_timestamp' in params
    assert 'api_key' in params
    assert 'api_format' in params
    assert 'api_kit' in params
    assert 'api_signature' in params

    request_params['api_nonce'] = params['api_nonce']
    request_params['api_timestamp'] = params['api_timestamp']
    request_params['api_key'] = params['api_key']
    request_params['api_format'] = params['api_format']
    request_params['api_kit'] = params['api_kit']

    # The logic before allowing array in the query string
    # The array in the query string will be like "key=[val1,val2]"
    base_str = '&'.join(['{}={}'.format(
        quote(str(key).encode('utf-8'), safe='~'),
        quote(str(value).encode('utf-8'), safe='~')
    ) for key, value in sorted(request_params.items())])

    assert params['api_signature'] != hashlib.sha1(
        '{}{}'.format(base_str, SECRET).encode('utf-8')).hexdigest()


    # The array in the query string will be like "key=val1&key=val2"
    params_for_sbs = list()
    for key, value in sorted(request_params.items()):
        key = quote(str(key).encode('utf-8'), safe='~')
        if isinstance(value, list):
            for item in value:
                item = quote(str(item).encode('utf-8'), safe='~')
                params_for_sbs.append(f"{key}={item}")
        else:
            value = quote(str(value).encode('utf-8'), safe='~')
            params_for_sbs.append(f"{key}={value}")

    # Construct Signature Base String
    base_str = "&".join(params_for_sbs)

    assert params['api_signature'] == hashlib.sha1(
        '{}{}'.format(base_str, SECRET).encode('utf-8')).hexdigest()
