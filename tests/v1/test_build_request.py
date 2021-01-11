# -*- coding: utf-8 -*-

import pytest
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


SIGNATURE_TEST_CASES = [
    {
        'request_params': {
            'a': 1,
            'b': 'two',
            'c3': 'Param 3',
            u'❄': u'⛄',
            't1': True,
            'n0': None,
        },
        'expected_query_string': 'a=1&api_format=json&api_key=API_KEY_VALUE&api_kit=py-2.0.0'
                                 '&api_nonce=API_NONCE_VALUE&api_timestamp=API_TIMESTAMP_VALUE'
                                 '&b=two&c3=Param%203&n0=None&t1=True&%E2%9D%84=%E2%9B%84',
    },
    {
        'request_params': {
            'a': 1,
            'b': 'two',
            'c3': 'Param 3',
            u'❄': u'⛄',
            't1': True,
            'n0': None,
            'test_array1': [1, 2, 3, 4],
            'test_array2': ["test item1", "test item2"],
        },
        'expected_query_string': 'a=1&api_format=json&api_key=API_KEY_VALUE&api_kit=py-2.0.0'
                                 '&api_nonce=API_NONCE_VALUE&api_timestamp=API_TIMESTAMP_VALUE'
                                 '&b=two&c3=Param%203&n0=None&t1=True&test_array1=1&test_array1=2'
                                 '&test_array1=3&test_array1=4&test_array2=test%20item1'
                                 '&test_array2=test%20item2&%E2%9D%84=%E2%9B%84',
    },
]
@pytest.mark.parametrize('test_case', SIGNATURE_TEST_CASES)
def test_signature_none_array_values_only(test_case):

    KEY = 'api_key'
    SECRET = 'api_secret'
    PATH = '/test/resource/show'

    request_params = test_case['request_params']

    jwp_client = jwplatform.v1.Client(KEY, SECRET)

    url, params = jwp_client._build_request(PATH, request_params)

    assert url == 'https://api.jwplatform.com/v1{}'.format(PATH)
    assert 'api_nonce' in params
    assert 'api_timestamp' in params
    assert 'api_key' in params
    assert 'api_format' in params
    assert 'api_kit' in params
    assert 'api_signature' in params

    base_str = test_case['expected_query_string']
    base_str = base_str.replace('API_KEY_VALUE', KEY)
    base_str = base_str.replace('API_NONCE_VALUE', str(params['api_nonce']))
    base_str = base_str.replace('API_TIMESTAMP_VALUE', str(params['api_timestamp']))

    assert params['api_signature'] == hashlib.sha1(
        '{}{}'.format(base_str, SECRET).encode('utf-8')).hexdigest()
