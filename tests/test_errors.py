# -*- coding: utf-8 -*-
from unittest.mock import patch

import pytest

from jwplatform.client import JWPlatformClient
from jwplatform.errors import ClientError, ServerError, UnexpectedStatusError, BadRequestError

from .mock import JWPlatformMock


def test_client_error():
    client = JWPlatformClient()

    with JWPlatformMock():
        with pytest.raises(ClientError):
            client.raw_request("POST", "/v2/test_client_error/")

def test_server_error():
    client = JWPlatformClient()

    with JWPlatformMock():
        with pytest.raises(ServerError):
            client.raw_request("POST", "/v2/test_server_error/")

def test_unknown_status_error():
    client = JWPlatformClient()

    with JWPlatformMock():
        with pytest.raises(UnexpectedStatusError):
            client.raw_request("POST", "/v2/test_unknown_status_error/")

def test_unknown_body_error():
    client = JWPlatformClient()

    with JWPlatformMock():
        try:
            client.raw_request("POST", "/v2/test_unknown_body_error/")
            pytest.fail("Expected to raise ClientError")
        except ClientError as ex:
            assert ex.errors is None

def test_error_code_access():
    client = JWPlatformClient()

    with JWPlatformMock():
        try:
            client.raw_request("POST", "/v2/test_bad_request/")
            pytest.fail("Expected to raise ClientError")
        except ClientError as ex:
            assert ex.has_error_code("invalid_body") is True
            assert ex.has_error_code("invalid_code") is False
            assert len(ex.get_errors_by_code("invalid_body")) == 1, ex.get_errors_by_code("invalid_body")
            assert len(ex.get_errors_by_code("invalid_code")) == 0, ex.get_errors_by_code("invalid_code")
            assert str(ex) == "JWPlatform API Error:\n\ninvalid_body: The provided request body is invalid.\n"

def test_specific_error_class():
    client = JWPlatformClient()

    with JWPlatformMock():
        with pytest.raises(BadRequestError):
            client.raw_request("POST", "/v2/test_bad_request/")
