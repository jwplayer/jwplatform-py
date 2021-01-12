# -*- coding: utf-8 -*-
import math
import sys
# import mock
import http.client
from hashlib import md5
from unittest import skip, TestCase
from unittest.mock import patch, mock_open, Mock
from http.client import RemoteDisconnected

from jwplatform.version import __version__
from jwplatform.client import JWPlatformClient, JWPLATFORM_API_HOST
import logging

# from .mock import JWPlatformMock
from jwplatform.upload import UploadType, MaxRetriesExceededError, S3UploadError, UploadContext
from tests.mock import JWPlatformMock, S3Mock


def _get_parts_responses(part_count):
    parts = [{"upload_link": "http://s3server/upload-link",
              'id': part_id + 1} for part_id in range(part_count)]
    result = {'page': 1, 'page_length': 10, 'total': 10, 'parts': parts}
    return result


class TestUploads(TestCase):
    file_content_mock_data_simple = b'some bytes'
    file_content_mock_data_large = b'some bytes' * 5 * 1024 * 1024
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    @patch("os.stat")
    @patch("builtins.open")
    def test_upload_method_is_direct_when_file_size_is_small(self, mock_file, os_stat):
        os_stat.return_value.st_size = 4 * 1024 * 1024
        client = JWPlatformClient()
        media_client_instance = client.Media
        file_absolute_path = "mock_file_path"
        with open(file_absolute_path, "rb") as file:
            kwargs = {'target_part_size': 10 * 1024 * 1024, 'retry_count': 10, 'site_id': 'siteDEid'}
            with JWPlatformMock():
                upload_context = media_client_instance.create_media_and_get_upload_context(file, **kwargs)
                self.assertTrue(upload_context.upload_method == UploadType.direct.value)
                mock_file.assert_called_with(file_absolute_path, "rb")
                os_stat.assert_called_once()

    @patch("os.stat")
    @patch("builtins.open")
    def test_upload_method_is_multipart_when_file_size_is_large(self, mock_file, os_stat):
        os_stat.return_value.st_size = 100 * 1024 * 1024
        client = JWPlatformClient()
        media_client_instance = client.Media
        file_absolute_path = "mock_file_path"
        with open(file_absolute_path, "rb") as file:
            kwargs = {'target_part_size': 10 * 1024 * 1024, 'retry_count': 10, 'site_id': 'siteDEid'}
            with JWPlatformMock() as mock_api:
                upload_context = media_client_instance.create_media_and_get_upload_context(file, **kwargs)
                self.assertTrue(upload_context.upload_method == UploadType.multipart.value)
                mock_file.assert_called_with(file_absolute_path, "rb")
                os_stat.assert_called_once()
                mock_api.createMedia.request_mock.assert_called_once()

    @patch("builtins.open", new_callable=mock_open, read_data=file_content_mock_data_simple)
    @patch("os.stat")
    @patch("jwplatform.upload._get_bytes_hash")
    @patch("jwplatform.upload._get_returned_hash")
    def test_upload_method_with_direct_upload(self, get_returned_hash, get_bytes_hash, os_stat, mock_file):

        file_hash = md5(self.file_content_mock_data_simple).hexdigest()
        get_bytes_hash.return_value = file_hash
        get_returned_hash.return_value = f'\"{file_hash}\"'
        os_stat.return_value.st_size = 5 * 1024 * 1024
        client = JWPlatformClient()
        media_client_instance = client.Media
        file_absolute_path = "mock_file_path"
        with open(file_absolute_path, "rb") as file:
            kwargs = {'target_part_size': 10 * 1024 * 1024, 'retry_count': 1, 'site_id': 'siteDEid'}
            with JWPlatformMock() as mock_api, S3Mock() as s3_api:
                upload_context = media_client_instance.create_media_and_get_upload_context(file, **kwargs)
                media_client_instance.upload(file, upload_context, **kwargs)
                self.assertTrue(upload_context.upload_method == UploadType.direct.value)
                mock_file.assert_called_with(file_absolute_path, "rb")
                os_stat.assert_called_once()
                mock_api.createMedia.request_mock.assert_called_once()
                s3_api.uploadToS3.request_mock.assert_called_once()

    @patch("builtins.open", new_callable=mock_open, read_data=file_content_mock_data_simple)
    @patch("os.stat")
    @patch("jwplatform.upload._get_bytes_hash")
    @patch("jwplatform.upload._get_returned_hash", return_value='wrong_hash')
    def test_upload_method_with_direct_upload_fails_hash_check(self, get_returned_hash, get_bytes_hash, os_stat,
                                                               mock_file):
        file_hash = md5(self.file_content_mock_data_simple).hexdigest()
        get_bytes_hash.return_value = file_hash
        os_stat.return_value.st_size = 5 * 1024 * 1024
        client = JWPlatformClient()
        media_client_instance = client.Media
        file_absolute_path = "mock_file_path"
        with self.assertRaises(MaxRetriesExceededError):
            with open(file_absolute_path, "rb") as file:
                kwargs = {'target_part_size': 10 * 1024 * 1024, 'retry_count': 1, 'site_id': 'siteDEid'}
                with JWPlatformMock() as mock_api, S3Mock() as s3_api:
                    upload_context = media_client_instance.create_media_and_get_upload_context(file, **kwargs)
                    media_client_instance.upload(file, upload_context, **kwargs)
                    s3_api.uploadToS3.request_mock.assert_not_called()
                    mock_api.completeUpload.request_mock.assert_not_called()
                    mock_file.assert_called_with(file_absolute_path, "rb")

    @patch("builtins.open", new_callable=mock_open, read_data=file_content_mock_data_simple)
    @patch("os.stat")
    @patch("jwplatform.upload._get_bytes_hash")
    @patch("jwplatform.upload._get_returned_hash")
    def test_upload_method_with_direct_upload_retries_on_failed_hash_check(self, get_returned_hash, get_bytes_hash,
                                                                           os_stat, mock_file):
        file_hash = md5(self.file_content_mock_data_simple).hexdigest()
        get_bytes_hash.return_value = file_hash
        get_returned_hash.side_effect = ['wrong-hash', 'wrong-hash', f'\"{file_hash}\"']
        os_stat.return_value.st_size = 5 * 1024 * 1024
        client = JWPlatformClient()
        media_client_instance = client.Media
        file_absolute_path = "mock_file_path"
        with open(file_absolute_path, "rb") as file:
            kwargs = {'target_part_size': 10 * 1024 * 1024, 'retry_count': 3, 'site_id': 'siteDEid'}
            with JWPlatformMock() as mock_api, S3Mock() as s3_api:
                upload_context = media_client_instance.create_media_and_get_upload_context(file, **kwargs)
                media_client_instance.upload(file, upload_context, **kwargs)
                self.assertTrue(upload_context.upload_method == UploadType.direct.value)
                mock_file.assert_called_with(file_absolute_path, "rb")
                self.assertEqual(get_returned_hash.call_count, 3)
                mock_api.createMedia.request_mock.assert_called_once()
                self.assertEqual(s3_api.uploadToS3.request_mock.call_count, 3)
                mock_file.assert_called_with(file_absolute_path, "rb")

    @patch("builtins.open", new_callable=mock_open, read_data=file_content_mock_data_simple)
    @patch("os.stat")
    @patch("jwplatform.upload._get_bytes_hash")
    @patch("jwplatform.upload._get_returned_hash")
    @patch("jwplatform.upload._upload_to_s3")
    def test_upload_method_with_direct_upload_retries_on_failed_s3_upload(self, s3_upload_response, get_returned_hash,
                                                                          get_bytes_hash, os_stat, mock_file):
        file_hash = md5(self.file_content_mock_data_simple).hexdigest()
        get_bytes_hash.return_value = file_hash
        get_returned_hash.return_value = f'\"{file_hash}\"'
        s3_upload_response.side_effect = [S3UploadError, S3UploadError, 'some_response']
        os_stat.return_value.st_size = 5 * 1024 * 1024
        client = JWPlatformClient()
        media_client_instance = client.Media
        file_absolute_path = "mock_file_path"
        with open(file_absolute_path, "rb") as file:
            kwargs = {'target_part_size': 10 * 1024 * 1024, 'retry_count': 5, 'site_id': 'siteDEid'}
            with JWPlatformMock() as mock_api:
                upload_context = media_client_instance.create_media_and_get_upload_context(file, **kwargs)
                media_client_instance.upload(file, upload_context, **kwargs)
                self.assertTrue(upload_context.upload_method == UploadType.direct.value)
                mock_file.assert_called_with(file_absolute_path, "rb")
                self.assertEqual(get_returned_hash.call_count, 1)
                mock_api.createMedia.request_mock.assert_called_once()
                self.assertEqual(s3_upload_response.call_count, 3)
                mock_file.assert_called_with(file_absolute_path, "rb")

    @patch("builtins.open", new_callable=mock_open, read_data=file_content_mock_data_simple)
    @patch("os.stat")
    @patch("jwplatform.upload._get_bytes_hash")
    @patch("jwplatform.upload._get_returned_hash")
    @patch("jwplatform.upload._upload_to_s3")
    def test_upload_method_with_direct_upload_throws_when_retries_exceeded_on_failed_s3_upload(self, s3_upload_response,
                                                                                               get_returned_hash,
                                                                                               get_bytes_hash, os_stat,
                                                                                               mock_file):
        file_hash = md5(self.file_content_mock_data_simple).hexdigest()
        get_bytes_hash.return_value = file_hash
        get_returned_hash.return_value = f'\"{file_hash}\"'
        s3_upload_response.side_effect = [S3UploadError, S3UploadError, S3UploadError]
        os_stat.return_value.st_size = 5 * 1024 * 1024
        client = JWPlatformClient()
        media_client_instance = client.Media
        file_absolute_path = "mock_file_path"
        with open(file_absolute_path, "rb") as file:
            kwargs = {'target_part_size': 10 * 1024 * 1024, 'retry_count': 3, 'site_id': 'siteDEid'}
            with JWPlatformMock() as mock_api:
                upload_context = media_client_instance.create_media_and_get_upload_context(file, **kwargs)
                with self.assertRaises(MaxRetriesExceededError):
                    media_client_instance.upload(file, upload_context, **kwargs)
                mock_api.completeUpload.request_mock.assert_not_called()
                mock_file.assert_called_with(file_absolute_path, "rb")

    @patch("builtins.open", new_callable=mock_open, read_data=file_content_mock_data_simple)
    @patch("os.stat")
    @patch("jwplatform.upload._get_bytes_hash")
    @patch("jwplatform.upload._get_returned_hash")
    @patch("jwplatform.upload._upload_to_s3")
    def test_upload_method_with_direct_upload_throws_on_unexpected_error(self, s3_upload_response,
                                                                         get_returned_hash,
                                                                         get_bytes_hash,
                                                                         os_stat,
                                                                         mock_file):
        file_hash = md5(self.file_content_mock_data_simple).hexdigest()
        get_bytes_hash.return_value = file_hash
        get_returned_hash.return_value = f'\"{file_hash}\"'
        s3_upload_response.side_effect = Exception
        os_stat.return_value.st_size = 5 * 1024 * 1024
        client = JWPlatformClient()
        media_client_instance = client.Media
        file_absolute_path = "mock_file_path"
        with open(file_absolute_path, "rb") as file:
            kwargs = {'target_part_size': 10 * 1024 * 1024, 'retry_count': 3, 'site_id': 'siteDEid'}
            with JWPlatformMock() as mock_api:
                upload_context = media_client_instance.create_media_and_get_upload_context(file, **kwargs)
                with self.assertRaises(Exception):
                    media_client_instance.upload(file, upload_context, **kwargs)
                mock_file.assert_called_with(file_absolute_path, "rb")

    @patch("builtins.open", new_callable=mock_open, read_data=file_content_mock_data_large)
    @patch("os.stat")
    @patch("jwplatform.upload._get_bytes_hash")
    @patch("jwplatform.upload._get_returned_hash")
    @patch("jwplatform.upload.MultipartUpload._get_uploaded_part_hash")
    @patch("jwplatform.upload.MultipartUpload._retrieve_part_links")
    def test_upload_method_with_multipart_upload_success(self, retrieve_part_links, get_uploaded_part_hash,
                                                         get_returned_hash, get_bytes_hash,os_stat, mock_file):
        file_hash = md5(self.file_content_mock_data_large).hexdigest()
        get_bytes_hash.return_value = file_hash
        os_stat.return_value.st_size = len(self.file_content_mock_data_large)
        target_part_size = 5 * 1024 * 1024
        part_count = math.ceil(len(self.file_content_mock_data_large) / target_part_size)
        get_uploaded_part_hash.return_value = None
        get_returned_hash.return_value = f'\"{file_hash}\"'
        retrieve_part_links.return_value = _get_parts_responses(part_count)
        client = JWPlatformClient()
        media_client_instance = client.Media
        file_absolute_path = "mock_file_path"
        with open(file_absolute_path, "rb") as file:
            kwargs = {'target_part_size': 5 * 1024 * 1024, 'retry_count': 3, 'base_url': JWPLATFORM_API_HOST,
                      'site_id': 'siteDEid'}
            with JWPlatformMock() as mock_api, S3Mock() as s3_api:
                upload_context = media_client_instance.create_media_and_get_upload_context(file, **kwargs)
                self.assertTrue(upload_context.upload_method == UploadType.multipart.value)
                media_client_instance.upload(file, upload_context, **kwargs)
                mock_file.assert_called_with(file_absolute_path, "rb")
                mock_api.createMedia.request_mock.assert_called_once()
                mock_api.completeUpload.request_mock.assert_called_once()
                self.assertEqual(get_uploaded_part_hash.call_count, part_count)
                self.assertEqual(get_returned_hash.call_count, part_count)
                retrieve_part_links.assert_called_once()
                self.assertEqual(s3_api.uploadToS3.request_mock.call_count, part_count)

    @patch("builtins.open", new_callable=mock_open, read_data=file_content_mock_data_large)
    @patch("os.stat")
    @patch("jwplatform.upload._get_bytes_hash")
    @patch("jwplatform.upload._get_returned_hash")
    @patch("jwplatform.upload.MultipartUpload._get_uploaded_part_hash")
    @patch("jwplatform.upload.MultipartUpload._retrieve_part_links")
    def test_upload_method_with_multipart_upload_failure_on_mismatched_upload_hash(self, retrieve_part_links,
                                                                                   get_uploaded_part_hash,
                                                                                   get_returned_hash,
                                                                                   get_bytes_hash, os_stat, mock_file):
        file_hash = md5(self.file_content_mock_data_large).hexdigest()
        get_bytes_hash.return_value = file_hash
        os_stat.return_value.st_size = len(self.file_content_mock_data_large)
        target_part_size = 5 * 1024 * 1024
        part_count = math.ceil(len(self.file_content_mock_data_large) / target_part_size)
        get_uploaded_part_hash.return_value = None
        get_returned_hash.return_value = f'\"wrong_hash\"'
        retrieve_part_links.return_value = _get_parts_responses(part_count)
        site_id = 'siteDEid'
        client = JWPlatformClient()
        media_client_instance = client.Media
        file_absolute_path = "mock_file_path"
        retry_count = 3
        with open(file_absolute_path, "rb") as file:
            kwargs = {'target_part_size': 5 * 1024 * 1024, 'retry_count': retry_count, 'base_url': JWPLATFORM_API_HOST,
                      'site_id': 'siteDEid'}
            with JWPlatformMock() as mock_api, S3Mock() as s3_api:
                upload_context = media_client_instance.create_media_and_get_upload_context(file, **kwargs)
                self.assertTrue(upload_context.upload_method == UploadType.multipart.value)
                with self.assertRaises(MaxRetriesExceededError):
                    media_client_instance.upload(file, upload_context, **kwargs)
                mock_file.assert_called_with(file_absolute_path, "rb")
                mock_api.createMedia.request_mock.assert_called_once()
                mock_api.completeUpload.request_mock.assert_not_called()
                self.assertEqual(get_uploaded_part_hash.call_count, retry_count)
                self.assertEqual(get_returned_hash.call_count, retry_count)
                retrieve_part_links.assert_called_once()
                self.assertEqual(s3_api.uploadToS3.request_mock.call_count, retry_count)

    @patch("builtins.open", new_callable=mock_open, read_data=file_content_mock_data_large)
    @patch("os.stat")
    @patch("jwplatform.upload._get_bytes_hash")
    @patch("jwplatform.upload._get_returned_hash")
    @patch("jwplatform.upload.MultipartUpload._retrieve_part_links")
    @patch("jwplatform.upload.MultipartUpload._get_uploaded_part_hash")
    def test_upload_method_with_multipart_upload_resume_success(self, get_uploaded_part_hash, retrieve_part_links,
                                                                get_returned_hash, get_bytes_hash, os_stat, mock_file):
        file_hash = md5(self.file_content_mock_data_large).hexdigest()
        get_bytes_hash.return_value = file_hash
        get_returned_hash.return_value = f'\"{file_hash}\"'
        get_uploaded_part_hash.return_value = file_hash
        os_stat.return_value.st_size = len(self.file_content_mock_data_large)
        target_part_size = 5 * 1024 * 1024
        part_count = len(self.file_content_mock_data_large) // target_part_size + 1
        retrieve_part_links.return_value = _get_parts_responses(part_count)
        site_id = 'siteDEid'
        client = JWPlatformClient()
        media_client_instance = client.Media
        file_absolute_path = "mock_file_path"
        with open(file_absolute_path, "rb") as file:
            kwargs = {'target_part_size': 5 * 1024 * 1024, 'retry_count': 3, 'base_url': JWPLATFORM_API_HOST,
                      'site_id': 'siteDEid'}
            with JWPlatformMock() as mock_api, S3Mock() as s3_api:
                upload_context = UploadContext(UploadType.multipart.value, 'NL3OL1JB', 'upload_token', None)
                media_client_instance.resume(file, upload_context, **kwargs)
                mock_file.assert_called_with(file_absolute_path, "rb")
                mock_api.createMedia.request_mock.assert_not_called()
                mock_api.completeUpload.request_mock.assert_called_once()
                retrieve_part_links.assert_called_once()
                s3_api.uploadToS3.request_mock.assert_not_called()

    @patch("builtins.open", new_callable=mock_open, read_data=file_content_mock_data_large)
    @patch("os.stat")
    @patch("jwplatform.upload._get_bytes_hash")
    @patch("jwplatform.upload._get_returned_hash")
    @patch("jwplatform.upload.MultipartUpload._retrieve_part_links")
    @patch("jwplatform.upload._upload_to_s3")
    def test_upload_method_with_multipart_upload_throws_when_retries_exceeded_on_failed_s3_upload(self,
                                                                                                  s3_upload_response,
                                                                                                  retrieve_part_links,
                                                                                                  get_returned_hash,
                                                                                                  get_bytes_hash,
                                                                                                  os_stat,
                                                                                                  mock_file):
        file_hash = md5(self.file_content_mock_data_large).hexdigest()
        get_bytes_hash.return_value = file_hash
        get_returned_hash.return_value = f'\"{file_hash}\"'
        os_stat.return_value.st_size = len(self.file_content_mock_data_large)
        target_part_size = 5 * 1024 * 1024
        part_count = len(self.file_content_mock_data_large) // target_part_size + 1
        retrieve_part_links.return_value = _get_parts_responses(part_count)
        s3_upload_response.side_effect = S3UploadError
        site_id = 'siteDEid'
        client = JWPlatformClient()
        media_client_instance = client.Media
        file_absolute_path = "mock_file_path"
        with open(file_absolute_path, "rb") as file:
            kwargs = {'target_part_size': 5 * 1024 * 1024, 'retry_count': 3, 'base_url': JWPLATFORM_API_HOST,
                      'site_id': 'siteDEid'}
            with JWPlatformMock() as mock_api, S3Mock() as s3_api:
                upload_context = media_client_instance.create_media_and_get_upload_context(file, **kwargs)
                self.assertTrue(upload_context.upload_method == UploadType.multipart.value)
                with self.assertRaises(MaxRetriesExceededError):
                    media_client_instance.upload(file, upload_context, **kwargs)
                mock_api.completeUpload.request_mock.assert_not_called()
                mock_file.assert_called_with(file_absolute_path, "rb")

    @patch("builtins.open", new_callable=mock_open, read_data=file_content_mock_data_large)
    @patch("os.stat")
    @patch("jwplatform.upload._get_bytes_hash")
    @patch("jwplatform.upload._get_returned_hash")
    @patch("jwplatform.upload.MultipartUpload._retrieve_part_links")
    @patch("jwplatform.upload._upload_to_s3")
    def test_upload_method_with_multipart_upload_throws_on_unexpected_error(self,
                                                                            s3_upload_response,
                                                                            retrieve_part_links,
                                                                            get_returned_hash,
                                                                            get_bytes_hash,
                                                                            os_stat,
                                                                            mock_file):
        file_hash = md5(self.file_content_mock_data_large).hexdigest()
        get_bytes_hash.return_value = file_hash
        get_returned_hash.return_value = f'\"{file_hash}\"'
        os_stat.return_value.st_size = len(self.file_content_mock_data_large)
        target_part_size = 5 * 1024 * 1024
        part_count = len(self.file_content_mock_data_large) // target_part_size + 1
        retrieve_part_links.return_value = _get_parts_responses(part_count)
        s3_upload_response.side_effect = Exception
        site_id = 'siteDEid'
        client = JWPlatformClient()
        media_client_instance = client.Media
        file_absolute_path = "mock_file_path"
        with open(file_absolute_path, "rb") as file:
            kwargs = {'target_part_size': 5 * 1024 * 1024, 'retry_count': 3, 'base_url': JWPLATFORM_API_HOST,
                      'site_id': 'siteDEid'}
            with JWPlatformMock() as mock_api, S3Mock() as s3_api:
                upload_context = media_client_instance.create_media_and_get_upload_context(file, **kwargs)
                self.assertTrue(upload_context.upload_method == UploadType.multipart.value)
                with self.assertRaises(Exception):
                    media_client_instance.upload(file, upload_context, **kwargs)
                mock_api.completeUpload.request_mock.assert_not_called()
                mock_file.assert_called_with(file_absolute_path, "rb")
                s3_upload_response.assert_called_once()
