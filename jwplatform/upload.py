import http.client
import logging
import os
import sys
from enum import Enum
from hashlib import md5
from urllib.parse import urlparse

MAX_PAGE_SIZE = 1000
MIN_PART_SIZE = 5 * 1024 * 1024


class UploadType(Enum):
    direct = "direct"
    multipart = "multipart"


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

    def __init__(self, client, upload_id: str, file, target_part_size, retry_count):
        self._upload_id = upload_id
        self._target_part_size = target_part_size
        self._upload_retry_count = retry_count
        self._file = file
        self._client = client
        self._logger = logging.getLogger(self.__class__.__name__)

    def upload(self):

        if self._target_part_size < MIN_PART_SIZE:
            raise ValueError(f"The part size has to be at least greater than {MIN_PART_SIZE} bytes.")

        filename = self._file.name
        file_size = os.stat(filename).st_size
        part_count = file_size // self._target_part_size + 1

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
            total_page_count = part_count // MAX_PAGE_SIZE + 1
            if total_page_count > 0:
                for page_number in range(1, total_page_count + 1):
                    batch_size = min(remaining_parts_count, MAX_PAGE_SIZE)
                    page_length = MAX_PAGE_SIZE
                    remaining_parts_count = remaining_parts_count - batch_size
                    query_params = {'page_length': page_length, 'page': page_number}
                    self._logger.debug(
                        f'calling list method with page_number:{page_number} and page_length:{page_length}.')
                    resp = self._client.list(resource_id=self._upload_id, subresource_name='parts',
                                             query_params=query_params)
                    body = resp.json_body
                    upload_links = body['parts']
                    for part_number in range(1, batch_size + 1):
                        bytes_chunk = self._file.read(self._target_part_size)
                        if part_number < batch_size and len(bytes_chunk) != self._target_part_size:
                            raise IOError("Failed to read enough bytes")
                        retry_count = 0
                        for _ in range(self._upload_retry_count):
                            try:
                                self._upload_part(bytes_chunk, part_number, upload_links)

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
                                        f" {part_number} of {part_count} for file {filename}.", err)
        except Exception as ex:
            self._file.seek(0, 0)
            self._logger.exception(ex)
            raise

    def _upload_part(self, bytes_chunk, part_number, upload_links):
        computed_hash = _get_bytes_hash(bytes_chunk)

        # Check if the file has already been uploaded and the hash matches. Return immediately without doing anything
        # if the hash matches.
        upload_hash = upload_links[part_number - 1]["etag"] if "etag" in upload_links[part_number - 1] else None
        # self._logger.debug(f'Part number {part_number}:{upload_hash}')
        if upload_hash and repr(upload_hash) == repr(f"{computed_hash}"):  # returned hash is not surrounded by '"'
            self._logger.debug(f"Part number {part_number} already uploaded. Skipping")
            return

        if "upload_link" not in upload_links[part_number - 1]:
            # self._logger.debug(f"Invalid upload link for part {part_number}.")
            raise KeyError(f"Invalid upload link for part {part_number}.")

        upload_link = upload_links[part_number - 1]["upload_link"]
        response = _upload_to_s3(bytes_chunk, upload_link)

        returned_hash = _get_returned_hash(response)
        if repr(returned_hash) != repr(f"\"{computed_hash}\""):  # The returned hash is surrounded by '"' character
            raise DataIntegrityError("The hash of the uploaded file does not match with the hash on the server.")

    def _mark_upload_completion(self):
        self._client.complete(self._upload_id)
        self._logger.info("Upload successful!")


class SingleUpload:

    def __init__(self, upload_link, file, retry_count):
        self._upload_link = upload_link
        self._upload_retry_count = retry_count
        self._file = file
        self._logger = logging.getLogger(self.__class__.__name__)

    def upload(self):
        bytes_chunk = self._file.read()
        computed_hash = _get_bytes_hash(bytes_chunk)
        retry_count = 0
        for _ in range(self._upload_retry_count):
            try:
                response = _upload_to_s3(bytes_chunk, self._upload_link)
                returned_hash = _get_returned_hash(response)
                print(returned_hash)
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
