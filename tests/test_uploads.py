# -*- coding: utf-8 -*-
import sys
# import mock
import http.client
from hashlib import md5
from unittest import skip, TestCase
from unittest.mock import patch, mock_open, Mock

from jwplatform import __version__
from jwplatform.client import JWPlatformClient
import logging

# from .mock import JWPlatformMock
from jwplatform.upload import UploadType
from tests.mock import JWPlatformMock
from tests.s3mock import S3Mock


class TestUploads(TestCase):
    # file_content_mock = b'some bytes'
    # file_hash = md5(file_content_mock).hexdigest()

    @patch("os.stat")
    def test_upload_method_is_direct_when_file_size_is_small(self, os_stat):
        file_content_mock = 'some bytes'
        os_stat.return_value.st_size = 4 * 1024 * 1024
        with patch("builtins.open", mock_open(read_data="data")) as mock_file:
            site_id = 'siteDEid'
            client = JWPlatformClient()
            media_client_instance = client.Media
            file_absolute_path = "mock_file_path"
            logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
            with open(file_absolute_path, "rb") as file:
                kwargs = {'target_part_size': 10 * 1024 * 1024, 'retry_count': 10}
                with JWPlatformMock():
                    context_dict = media_client_instance.create_media_for_upload(site_id, file, **kwargs)
                    self.assertTrue(context_dict['upload_method'] == UploadType.direct.value)
                    mock_file.assert_called_with(file_absolute_path, "rb")

    @patch("os.stat")
    def test_upload_method_is_multipart_when_file_size_is_large(self, os_stat):
        file_content_mock = 'some bytes'
        os_stat.return_value.st_size = 100 * 1024 * 1024
        with patch("builtins.open", mock_open(read_data="data")) as mock_file:
            site_id = 'siteDEid'
            client = JWPlatformClient()
            media_client_instance = client.Media
            file_absolute_path = "mock_file_path"
            logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
            with open(file_absolute_path, "rb") as file:
                kwargs = {'target_part_size': 10 * 1024 * 1024, 'retry_count': 10}
                with JWPlatformMock() as mock_api:
                    context_dict = media_client_instance.create_media_for_upload(site_id, file, **kwargs)
                    self.assertTrue(context_dict['upload_method'] == UploadType.multipart.value)
                    mock_file.assert_called_with(file_absolute_path, "rb")
                    mock_api.createMedia.request_mock.assert_called_once()

    @patch("os.stat")
    @patch("jwplatform.upload._get_bytes_hash")
    @patch("jwplatform.upload._get_returned_hash")
    def test_upload_method_with_direct_upload(self, get_returned_hash, get_bytes_hash, os_stat):
        file_content_mock = b'some bytes'
        file_hash = md5(file_content_mock).hexdigest()
        get_bytes_hash.return_value = file_hash
        get_returned_hash.return_value = f'\"{file_hash}\"'
        os_stat.return_value.st_size = 5 * 1024 * 1024
        with patch("builtins.open", mock_open(read_data=file_content_mock)) as mock_file:
            site_id = 'siteDEid'
            client = JWPlatformClient()
            media_client_instance = client.Media
            file_absolute_path = "mock_file_path"
            logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
            with open(file_absolute_path, "rb") as file:
                kwargs = {'target_part_size': 10 * 1024 * 1024, 'retry_count': 1}
                with JWPlatformMock() as mock_api, S3Mock() as s3_api:
                    context_dict = media_client_instance.create_media_for_upload(site_id, file, **kwargs)
                    media_client_instance.upload(file, context_dict, **kwargs)
                    self.assertTrue(context_dict['upload_method'] == UploadType.direct.value)
                    mock_file.assert_called_with(file_absolute_path, "rb")
                    mock_api.createMedia.request_mock.assert_called_once()
                    s3_api.uploadToS3.request_mock.assert_called_once()

# TestUploads().test_upload_method_is_direct_when_file_size_is_small()
