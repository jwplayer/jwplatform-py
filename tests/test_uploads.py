# -*- coding: utf-8 -*-
import sys
import mock
from unittest import skip, TestCase
from unittest.mock import patch, mock_open

from jwplatform import __version__
from jwplatform.client import JWPlatformClient
import logging

# from .mock import JWPlatformMock
from jwplatform.upload import UploadType
from tests.mock import JWPlatformMock


class TestUploads(TestCase):

    @mock.patch("os.stat")
    def test_upload_method_is_direct_when_file_size_is_small(self, os_stat):
        file_content_mock = 'some bytes'
        os_stat.return_value.st_size = 4 * 1024 * 1024
        with patch("builtins.open", mock_open(read_data="data")) as mock_file:

            site_id = 'site_id'
            client = JWPlatformClient()
            media_client_instance = client.Media
            file_absolute_path = "mock_file_path"
            logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
            with open(file_absolute_path, "rb") as file:
                kwargs = {'target_part_size': 10 * 1024 * 1024, 'retry_count': 10}
                with JWPlatformMock():
                    response = client.raw_request("POST", "/v2/media/")
                context_dict = media_client_instance.create_media_for_upload(site_id, file, **kwargs)
            self.assertTrue(context_dict['upload_method'] == UploadType.direct.value)
            mock_file.assert_called_with(file_absolute_path, "rb")

    @mock.patch("os.stat")
    def test_upload_method_is_multipart_when_file_size_is_large(self, os_stat):
        file_content_mock = 'some bytes'
        os_stat.return_value.st_size = 100 * 1024 * 1024
        with patch("builtins.open", mock_open(read_data="data")) as mock_file:
            site_id = 'site_id'
            client = JWPlatformClient()
            media_client_instance = client.Media
            file_absolute_path = "mock_file_path"
            logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
            with open(file_absolute_path, "rb") as file:
                kwargs = {'target_part_size': 10 * 1024 * 1024, 'retry_count': 10}
                with JWPlatformMock():
                    response = client.raw_request("POST", "/v2/media/")
                context_dict = media_client_instance.create_media_for_upload(site_id, file, **kwargs)
            self.assertTrue(context_dict['upload_method'] == UploadType.multipart.value)
            mock_file.assert_called_with(file_absolute_path, "rb")




