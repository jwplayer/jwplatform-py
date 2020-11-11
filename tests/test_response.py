# -*- coding: utf-8 -*-
from unittest.mock import patch

from jwplatform.client import JWPlatformClient

from .mock import JWPlatformMock


def test_success_response_object():
    client = JWPlatformClient()

    with JWPlatformMock():
        response = client.raw_request("POST", "/v2/test_request/")

    assert response.status == 200
    assert response.body == b'{"field": "value"}'
    assert response.json_body["field"] == "value"

def test_resource_response():
    client = JWPlatformClient()

    with JWPlatformMock():
        response = client.Media.get(site_id="testsite", media_id="mediaid1")

    assert response.status == 200
    assert response.json_body["id"] == "mediaid1"
    assert response.json_body["type"] == "media"
    assert isinstance(response, client.Media.__class__), response.__class__.__name__

def test_resources_response():
    client = JWPlatformClient()

    with JWPlatformMock():
        response = client.Media.list(site_id="testsite")

    assert response.status == 200
    assert len(response) == 1
    for media in response:
        assert media["id"] == "mediaid1"
        assert media["type"] == "media"
    assert isinstance(response, client.Media.__class__), response.__class__.__name__
