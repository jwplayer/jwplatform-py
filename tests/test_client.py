# -*- coding: utf-8 -*-
from unittest.mock import patch

from jwplatform import __version__
from jwplatform.client import JWPlatformClient

from .mock import JWPlatformMock


def test_raw_request_sends():
    client = JWPlatformClient()

    with JWPlatformMock() as mock_api:
        client.raw_request("POST", "/v2/test_request/")

    mock_api.testRequest.request_mock.assert_called_once()

def test_request_sends():
    client = JWPlatformClient()

    with JWPlatformMock() as mock_api:
        client.request("POST", "/v2/test_request/")

    mock_api.testRequest.request_mock.assert_called_once()

def test_request_modifies_input():
    client = JWPlatformClient(secret="test_secret")

    with patch.object(client, 'raw_request') as mock_raw_request:
        client.request(
            "POST", "/v2/test_request/",
            body={"field": "value"},
            query_params={"param": "value"}
        )

    mock_raw_request.assert_called_once()
    kwargs = mock_raw_request.call_args[1]
    assert kwargs["method"] == "POST"
    assert kwargs["url"] == "/v2/test_request/?param=value"
    assert kwargs["body"] == '{"field": "value"}'
    assert kwargs["headers"]["User-Agent"] == f"jwplatform_client-python/{__version__}"
    assert kwargs["headers"]["Content-Type"] == "application/json"
    assert kwargs["headers"]["Authorization"] == "Bearer test_secret"
