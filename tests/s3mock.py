# -*- coding: utf-8 -*-
from networktest.mock import HttpApiMock, HttpApiMockEndpoint


class S3Mock(HttpApiMock):
    hostnames = ['s3server']

    endpoints = [
        HttpApiMockEndpoint(
            operation_id='uploadToS3',
            match_pattern=b'^PUT ',
            response=lambda _: (200, None),
        )
    ]