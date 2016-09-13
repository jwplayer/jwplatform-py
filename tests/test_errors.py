# -*- coding: utf-8 -*-

import re
import json
import pytest
import jwplatform
import responses


SUPPORTED_ERROR_CASES = [
    {
        'http_status': 400,
        'response': {
            'status': 'error',
            'code': 'UnknownError',
            'title': 'An Unknown Error occurred',
            'message': ''
        },
        'expected_exception': jwplatform.errors.JWPlatformUnknownError
    },
    {
        'http_status': 404,
        'response': {
            'status': 'error',
            'code': 'NotFound',
            'title': 'Not Found',
            'message': 'Item not found'
        },
        'expected_exception': jwplatform.errors.JWPlatformNotFoundError
    },
    {
        'http_status': 400,
        'response': {
            'status': 'error',
            'code': 'NoMethod',
            'title': 'No Method Specified',
            'message': ''
        },
        'expected_exception': jwplatform.errors.JWPlatformNoMethodError
    },
    {
        'http_status': 501,
        'response': {
            'status': 'error',
            'code': 'NotImplemented',
            'title': 'Method Not Implemented',
            'message': ''
        },
        'expected_exception': jwplatform.errors.JWPlatformNotImplementedError
    },
    {
        'http_status': 405,
        'response': {
            'status': 'error',
            'code': 'NotSupported',
            'title': 'Method or parameter not supported',
            'message': ''
        },
        'expected_exception': jwplatform.errors.JWPlatformNotSupportedError
    },
    {
        'http_status': 500,
        'response': {
            'status': 'error',
            'code': 'CallFailed',
            'title': 'Call Failed',
            'message': ''
        },
        'expected_exception': jwplatform.errors.JWPlatformCallFailedError
    },
    {
        'http_status': 503,
        'response': {
            'status': 'error',
            'code': 'CallUnavailable',
            'title': 'Call Unavailable',
            'message': ''
        },
        'expected_exception': jwplatform.errors.JWPlatformCallUnavailableError
    },
    {
        'http_status': 400,
        'response': {
            'status': 'error',
            'code': 'CallInvalid',
            'title': 'Call Invalid',
            'message': ''
        },
        'expected_exception': jwplatform.errors.JWPlatformCallInvalidError
    },
    {
        'http_status': 400,
        'response': {
            'status': 'error',
            'code': 'ParameterMissing',
            'title': 'Missing Parameter',
            'message': 'Parameter is missing'
        },
        'expected_exception': jwplatform.errors.JWPlatformParameterMissingError
    },
    {
        'http_status': 400,
        'response': {
            'status': 'error',
            'code': 'ParameterEmpty',
            'title': 'Empty Parameter',
            'message': ''
        },
        'expected_exception': jwplatform.errors.JWPlatformParameterEmptyError
    },
    {
        'http_status': 400,
        'response': {
            'status': 'error',
            'code': 'ParameterEncodingError',
            'title': 'Parameter Encoding Error',
            'message': ''
        },
        'expected_exception': jwplatform.errors.JWPlatformParameterEncodingError
    },
    {
        'http_status': 400,
        'response': {
            'status': 'error',
            'code': 'ParameterInvalid',
            'title': 'Invalid Parameter',
            'message': ''
        },
        'expected_exception': jwplatform.errors.JWPlatformParameterInvalidError
    },
    {
        'http_status': 412,
        'response': {
            'status': 'error',
            'code': 'PreconditionFailed',
            'title': 'Precondition Failed',
            'message': ''
        },
        'expected_exception': jwplatform.errors.JWPlatformPreconditionFailedError
    },
    {
        'http_status': 409,
        'response': {
            'status': 'error',
            'code': 'ItemAlreadyExists',
            'title': 'Item Already Exists',
            'message': ''
        },
        'expected_exception': jwplatform.errors.JWPlatformItemAlreadyExistsError
    },
    {
        'http_status': 403,
        'response': {
            'status': 'error',
            'code': 'PermissionDenied',
            'title': 'Permission Denied',
            'message': ''
        },
        'expected_exception': jwplatform.errors.JWPlatformPermissionDeniedError
    },
    {
        'http_status': 500,
        'response': {
            'status': 'error',
            'code': 'DatabaseError',
            'title': 'Database Error',
            'message': ''
        },
        'expected_exception': jwplatform.errors.JWPlatformDatabaseError
    },
    {
        'http_status': 500,
        'response': {
            'status': 'error',
            'code': 'IntegrityError',
            'title': 'Integrity Error',
            'message': ''
        },
        'expected_exception': jwplatform.errors.JWPlatformIntegrityError
    },
    {
        'http_status': 400,
        'response': {
            'status': 'error',
            'code': 'DigestMissing',
            'title': 'Digest Missing',
            'message': ''
        },
        'expected_exception': jwplatform.errors.JWPlatformDigestMissingError
    },
    {
        'http_status': 400,
        'response': {
            'status': 'error',
            'code': 'DigestInvalid',
            'title': 'Digest Invalid',
            'message': ''
        },
        'expected_exception': jwplatform.errors.JWPlatformDigestInvalidError
    },
    {
        'http_status': 400,
        'response': {
            'status': 'error',
            'code': 'FileUploadFailed',
            'title': 'File Upload Failed',
            'message': ''
        },
        'expected_exception': jwplatform.errors.JWPlatformFileUploadFailedError
    },
    {
        'http_status': 400,
        'response': {
            'status': 'error',
            'code': 'FileSizeMissing',
            'title': 'File Size Missing',
            'message': ''
        },
        'expected_exception': jwplatform.errors.JWPlatformFileSizeMissingError
    },
    {
        'http_status': 400,
        'response': {
            'status': 'error',
            'code': 'FileSizeInvalid',
            'title': 'File Size Invalid',
            'message': ''
        },
        'expected_exception': jwplatform.errors.JWPlatformFileSizeInvalidError
    },
    {
        'http_status': 500,
        'response': {
            'status': 'error',
            'code': 'InternalError',
            'title': 'Internal Error',
            'message': ''
        },
        'expected_exception': jwplatform.errors.JWPlatformInternalError
    },
    {
        'http_status': 400,
        'response': {
            'status': 'error',
            'code': 'ApiKeyMissing',
            'title': 'User Key Missing',
            'message': ''
        },
        'expected_exception': jwplatform.errors.JWPlatformApiKeyMissingError
    },
    {
        'http_status': 400,
        'response': {
            'status': 'error',
            'code': 'ApiKeyInvalid',
            'title': 'User Key Invalid',
            'message': ''
        },
        'expected_exception': jwplatform.errors.JWPlatformApiKeyInvalidError
    },
    {
        'http_status': 400,
        'response': {
            'status': 'error',
            'code': 'TimestampMissing',
            'title': 'Timestamp Missing',
            'message': ''
        },
        'expected_exception': jwplatform.errors.JWPlatformTimestampMissingError
    },
    {
        'http_status': 400,
        'response': {
            'status': 'error',
            'code': 'TimestampInvalid',
            'title': 'Timestamp Invalid',
            'message': ''
        },
        'expected_exception': jwplatform.errors.JWPlatformTimestampInvalidError
    },
    {
        'http_status': 403,
        'response': {
            'status': 'error',
            'code': 'TimestampExpired',
            'title': 'Timestamp Expired',
            'message': ''
        },
        'expected_exception': jwplatform.errors.JWPlatformTimestampExpiredError
    },
    {
        'http_status': 400,
        'response': {
            'status': 'error',
            'code': 'NonceMissing',
            'title': 'Nonce Missing',
            'message': ''
        },
        'expected_exception': jwplatform.errors.JWPlatformNonceMissingError
    },
    {
        'http_status': 400,
        'response': {
            'status': 'error',
            'code': 'NonceInvalid',
            'title': 'Nonce Invalid',
            'message': ''
        },
        'expected_exception': jwplatform.errors.JWPlatformNonceInvalidError
    },
    {
        'http_status': 400,
        'response': {
            'status': 'error',
            'code': 'SignatureMissing',
            'title': 'Signature Missing',
            'message': ''
        },
        'expected_exception': jwplatform.errors.JWPlatformSignatureMissingError
    },
    {
        'http_status': 400,
        'response': {
            'status': 'error',
            'code': 'SignatureInvalid',
            'title': 'Signature Invalid',
            'message': '400'
        },
        'expected_exception': jwplatform.errors.JWPlatformSignatureInvalidError
    },
    {
        'http_status': 429,
        'response': {
            'status': 'error',
            'code': 'RateLimitExceeded',
            'title': 'Rate Limit Exceeded',
            'message': ''
        },
        'expected_exception': jwplatform.errors.JWPlatformRateLimitExceededError
    },
    {
        'http_status': 500,
        'response': {
            'status': 'error',
            'message': 'New unhandled error',
            'code': 'NewError',
            'title': 'New Error'
        },
        'expected_exception': jwplatform.errors.JWPlatformUnknownError
    }
]


@responses.activate
@pytest.mark.parametrize('test_case', SUPPORTED_ERROR_CASES)
def test_supported_errors_parsing(test_case):
    url_expr = re.compile(r'https?://api\.test\.tst/v1/error\?.*')

    responses.add(
        responses.GET, url_expr,
        status=test_case['http_status'],
        content_type='application/json',
        body=json.dumps(test_case['response']))

    jwp_client = jwplatform.Client('api_key', 'api_secret', host='api.test.tst')

    with pytest.raises(test_case['expected_exception']) as err:
        jwp_client.error()

    assert err.value.message == test_case['response']['message']


@responses.activate
def test_empty_response_parsing():
    url_expr = re.compile(r'https?://api\.test\.tst/v1/error\?.*')

    responses.add(
        responses.GET, url_expr,
        status=500,
        content_type='application/json',
        body='')

    jwp_client = jwplatform.Client('api_key', 'api_secret', host='api.test.tst')

    with pytest.raises(jwplatform.errors.JWPlatformUnknownError) as err:
        jwp_client.error()

    assert err.value.message == 'Not a valid JSON string: '


@responses.activate
def test_non_json_response_parsing():
    url_expr = re.compile(r'https?://api\.test\.tst/v1/error\?.*')

    responses.add(
        responses.GET, url_expr,
        status=502,
        content_type='text/html',
        body='502 Bad Gateway')

    jwp_client = jwplatform.Client('api_key', 'api_secret', host='api.test.tst')

    with pytest.raises(jwplatform.errors.JWPlatformUnknownError) as err:
        jwp_client.error()

    assert err.value.message == 'Not a valid JSON string: 502 Bad Gateway'
