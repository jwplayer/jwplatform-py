# -*- coding: utf-8 -*-
from networktest.mock import HttpApiMock, HttpApiMockEndpoint

from jwplatform.client import JWPLATFORM_API_HOST


class JWPlatformMock(HttpApiMock):
    hostnames = [JWPLATFORM_API_HOST]

    endpoints = [
        HttpApiMockEndpoint(
            operation_id='testRequest',
            match_pattern=b'^POST /v2/test_request/',
            response=lambda _: (200, {"field": "value"}),
        ),
        HttpApiMockEndpoint(
            operation_id='testClientError',
            match_pattern=b'^POST /v2/test_bad_request/',
            response=lambda _: (400, {
                "errors": [{
                    "code": "invalid_body",
                    "description": "The provided request body is invalid.",
                }]
            }),
        ),
        HttpApiMockEndpoint(
            operation_id='testClientError',
            match_pattern=b'^POST /v2/test_client_error/',
            response=lambda _: (499, {
                "errors": [{
                    "code": "invalid_body",
                    "description": "The provided request body is invalid.",
                }]
            }),
        ),
        HttpApiMockEndpoint(
            operation_id='testServerError',
            match_pattern=b'^POST /v2/test_server_error/',
            response=lambda _: (599, {
                "errors": [{
                    "code": "server_error",
                    "description": "Something unexpectedly went wrong.",
                }]
            }),
        ),
        HttpApiMockEndpoint(
            operation_id='testUnknownStatusError',
            match_pattern=b'^POST /v2/test_unknown_status_error/',
            response=lambda _: (999, None)
        ),
        HttpApiMockEndpoint(
            operation_id='testUnknownBodyError',
            match_pattern=b'^POST /v2/test_unknown_body_error/',
            response=lambda _: (400, "unexpected")
        ),
        HttpApiMockEndpoint(
            operation_id='getMedia',
            match_pattern=b'^GET /v2/sites/(?P<site_id>[A-Za-z0-9]{8}?)/media/(?P<media_id>[A-Za-z0-9]{8}?)/',
            response=lambda groups: (200, {
                "id": groups["media_id"],
                "type": "media",
            })
        ),
        HttpApiMockEndpoint(
            operation_id='listMedia',
            match_pattern=b'^GET /v2/sites/(?P<site_id>[A-Za-z0-9]{8}?)/media/',
            response=lambda groups: (200, {
                "media": [{
                    "id": "mediaid1",
                    "type": "media",
                }],
            })
        )
    ]
