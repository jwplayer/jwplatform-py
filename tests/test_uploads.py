# -*- coding: utf-8 -*-
from unittest.mock import patch

from jwplatform import __version__
from jwplatform.client import JWPlatformClient

# from .mock import JWPlatformMock


def test_upload(api_secret):
    media_client_instance = JWPlatformClient(secret=api_secret).Media
    site_id = '3Flf1waG'
    file_absolute_path = "../Origins.webm"
    with open(file_absolute_path, "rb") as file:
        kwargs = {'base_url':'upload-dev.jwplayer.com', 'target_part_size': 7 * 1024 * 1024}
        upload_handler = media_client_instance.get_upload_handler(site_id, file, **kwargs)
        upload_handler.upload()

api_secret = ""
test_upload(api_secret)

