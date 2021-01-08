import http.client
import logging
import math
import os
import sys
from enum import Enum
from hashlib import md5
from urllib.parse import urlparse

MAX_PAGE_SIZE = 1000
MIN_PART_SIZE = 5 * 1024 * 1024
UPLOAD_BASE_URL = 'upload.jwplayer.com'


class UploadType(Enum):
    direct = "direct"
    multipart = "multipart"


class UploadContext:

    def __init__(self, upload_method, upload_id, upload_token, direct_link):
        self._upload_method = upload_method
        self._upload_id = upload_id
        self._upload_token = upload_token
        self._direct_link = direct_link

    @property
    def upload_method(self):
        return self._upload_method

    @upload_method.setter
    def upload_method(self, value):
        self._upload_method = value

    @property
    def upload_id(self):
        return self._upload_id

    @upload_id.setter
    def upload_id(self, value):
        self._upload_id = value

    @property
    def upload_token(self):
        return self._upload_token

    @upload_token.setter
    def upload_token(self, value):
        self._upload_token = value

    @property
    def direct_link(self):
        return self._direct_link

    @direct_link.setter
    def direct_link(self, value):
        self._direct_link = value


def _upload_to_s3(bytes_chunk, upload_link):
    url_metadata = urlparse(upload_link)
    if url_metadata.scheme in 'https':
        connection = http.client.HTTPSConnection(host=url_metadata.hostname)
    else:
        connection = http.client.HTTPConnection(host=url_metadata.hostname)

    connection.request('PUT', upload_link, body=bytes_chunk)
    response = connection.getresponse()
    if 200 <= response.status <= 299:
        return response

    raise S3UploadError(response)


def _get_bytes_hash(bytes_chunk):
    return md5(bytes_chunk).hexdigest()


def _get_returned_hash(response):
    return response.headers['ETag']


class MultipartUpload:

    def __init__(self, client, upload_id: str, file, target_part_size, retry_count, upload_context: UploadContext):
        self._upload_id = upload_id
        self._target_part_size = target_part_size
        self._upload_retry_count = retry_count
        self._file = file
        self._client = client
        self._logger = logging.getLogger(self.__class__.__name__)
        self._upload_context = upload_context

    @property
    def upload_context(self):
        return self._upload_context

    @upload_context.setter
    def upload_context(self, value):
        self._upload_context = value

    def upload(self):

        if self._target_part_size < MIN_PART_SIZE:
            raise ValueError(f"The part size has to be at least greater than {MIN_PART_SIZE} bytes.")

        filename = self._file.name
        file_size = os.stat(filename).st_size
        part_count = math.ceil(file_size / self._target_part_size)

        if part_count > 10000:
            raise ValueError(f"The given file cannot be divided into more than 10000 parts. Please try increasing the "
                             f"target part size.")

        # Upload the parts
        self._upload_parts(part_count)

        # Mark upload as complete
        self._mark_upload_completion()

    def _upload_parts(self, part_count):
        try:
            filename = self._file.name
            remaining_parts_count = part_count
            total_page_count = math.ceil(part_count / MAX_PAGE_SIZE)
            for page_number in range(1, total_page_count + 1):
                batch_size = min(remaining_parts_count, MAX_PAGE_SIZE)
                page_length = MAX_PAGE_SIZE
                remaining_parts_count = remaining_parts_count - batch_size
                query_params = {'page_length': page_length, 'page': page_number}
                self._logger.debug(
                    f'calling list method with page_number:{page_number} and page_length:{page_length}.')
                body = self._retrieve_part_links(query_params)
                upload_links = body['parts']
                for returned_part in upload_links[:batch_size]:
                    part_number = returned_part['id']
                    bytes_chunk = self._file.read(self._target_part_size)
                    if part_number < batch_size and len(bytes_chunk) != self._target_part_size:
                        raise IOError("Failed to read enough bytes")
                    retry_count = 0
                    for _ in range(self._upload_retry_count):
                        try:
                            self._upload_part(bytes_chunk, part_number, returned_part)
                            self._logger.debug(
                                f"Successfully uploaded part {(page_number - 1) * MAX_PAGE_SIZE + part_number} "
                                f"of {part_count} for upload id {self._upload_id}")
                            break
                        except (DataIntegrityError, PartUploadError, OSError) as err:
                            self._logger.warning(err)
                            retry_count = retry_count + 1
                            self._logger.warning(
                                f"Encountered error upload part {(page_number - 1) * MAX_PAGE_SIZE + part_number} "
                                f"of {part_count} for file {filename}.")
                            if retry_count >= self._upload_retry_count:
                                self._file.seek(0, 0)
                                raise MaxRetriesExceededError(
                                    f"Max retries ({self._upload_retry_count}) exceeded while uploading part"
                                    f" {part_number} of {part_count} for file {filename}.") from err
        except Exception as ex:
            self._file.seek(0, 0)
            self._logger.exception(ex)
            raise

    def _retrieve_part_links(self, query_params):
        resp = self._client.list(resource_id=self._upload_id, subresource_name='parts',
                                 query_params=query_params)
        return resp.json_body

    def _upload_part(self, bytes_chunk, part_number, returned_part):
        computed_hash = _get_bytes_hash(bytes_chunk)

        # Check if the file has already been uploaded and the hash matches. Return immediately without doing anything
        # if the hash matches.
        upload_hash = self._get_uploaded_part_hash(returned_part)
        if upload_hash and (repr(upload_hash) == repr(f"{computed_hash}")):  # returned hash is not surrounded by '"'
            self._logger.debug(f"Part number {part_number} already uploaded. Skipping")
            return
        elif upload_hash:
            raise FileExistsError(f'The file part {part_number} has been uploaded but the hash of the uploaded part '
                                  f'does not match the hash of the current part read. Aborting.')

        if "upload_link" not in returned_part:
            raise KeyError(f"Invalid upload link for part {part_number}.")

        returned_part = returned_part["upload_link"]
        response = _upload_to_s3(bytes_chunk, returned_part)

        returned_hash = _get_returned_hash(response)
        if repr(returned_hash) != repr(f"\"{computed_hash}\""):  # The returned hash is surrounded by '"' character
            raise DataIntegrityError("The hash of the uploaded file does not match with the hash on the server.")

    def _get_uploaded_part_hash(self, upload_link):
        upload_hash = upload_link.get("etag")
        return upload_hash

    def _mark_upload_completion(self):
        self._client.complete(self._upload_id)
        self._logger.info("Upload successful!")


class SingleUpload:

    def __init__(self, upload_link, file, retry_count, upload_context: UploadContext):
        self._upload_link = upload_link
        self._upload_retry_count = retry_count
        self._file = file
        self._logger = logging.getLogger(self.__class__.__name__)
        self._upload_context = upload_context

    @property
    def upload_context(self):
        return self._upload_context

    @upload_context.setter
    def upload_context(self, value):
        self._upload_context = value

    def upload(self):
        self._logger.debug(f"Starting to upload file:{self._file.name}")
        bytes_chunk = self._file.read()
        computed_hash = _get_bytes_hash(bytes_chunk)
        retry_count = 0
        for _ in range(self._upload_retry_count):
            try:
                response = _upload_to_s3(bytes_chunk, self._upload_link)
                returned_hash = _get_returned_hash(response)
                if repr(returned_hash) != repr(
                        f"\"{computed_hash}\""):  # The returned hash is surrounded by '"' character
                    raise DataIntegrityError(
                        "The hash of the uploaded file does not match with the hash on the server.")
                self._logger.debug(f"Successfully uploaded file {self._file.name}.")
                return
            except (IOError, PartUploadError, DataIntegrityError, OSError) as err:
                self._logger.warning(err)
                self._logger.exception(err, stack_info=True)
                self._logger.warning(f"Encountered error uploading file {self._file.name}.")
                retry_count = retry_count + 1
                if retry_count >= self._upload_retry_count:
                    self._file.seek(0, 0)
                    raise MaxRetriesExceededError(f"Max retries exceeded while uploading file {self._file.name}")

            except Exception as ex:
                self._file.seek(0, 0)
                self._logger.exception(ex)
                raise


class DataIntegrityError(Exception):
    pass


class MaxRetriesExceededError(Exception):
    pass


class PartUploadError(Exception):
    pass


class S3UploadError(PartUploadError):
    pass
