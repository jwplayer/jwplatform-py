import http.client
import logging
import os
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

        # Get the part links
        upload_links = self._get_pre_signed_part_links(part_count, filename)

        # Mark upload as complete
        self._mark_upload_completion()

    def _get_pre_signed_part_links(self, part_count, filename):
        remaining_parts_count = part_count
        total_page_count = part_count // MAX_PAGE_SIZE + 1
        if total_page_count > 0:
            for page_number in range(1, total_page_count + 1):
                batch_size = min(remaining_parts_count, MAX_PAGE_SIZE)
                page_length = batch_size
                remaining_parts_count = remaining_parts_count - batch_size
                query_params = {'page_length': page_length, 'page': page_number}
                resp = self._client.list(resource_name='uploads', resource_id=self._upload_id, subresource_name='parts',
                                         query_params=query_params)
                body = resp.json_body
                upload_links = body['parts']
                mini_batch_size = page_length
                for part_number in range(1, mini_batch_size + 1):
                    bytes_chunk = self._file.read(self._target_part_size)
                    if part_number < mini_batch_size and len(bytes_chunk) != self._target_part_size:
                        raise IOError("Failed to read enough bytes")
                    retry_count = 0
                    for _ in range(self._upload_retry_count):
                        try:
                            self._upload_part(bytes_chunk, part_number, upload_links)
                            break
                        except (DataIntegrityError, PartUploadError) as err:
                            self._logger.warning(err)
                            if retry_count >= self._upload_retry_count:
                                raise MaxRetriesExceededError(
                                    f"Max retries ({self._upload_retry_count}) exceeded while uploading part"
                                    f" {part_number} of {part_count} for file {filename}.", err)
                            self._logger.warning(
                                f"Encountered error upload part {part_number} of {part_count} for file "
                                f"{filename}. Retrying.")
                            retry_count = retry_count + 1

    def _upload_part(self, bytes_chunk, part_number, upload_links):
        # Add a S3 server-side checksum validation too if possible.
        computed_hash = md5(bytes_chunk).hexdigest()

        # Check if the file has already been uploaded and the hash matches. Return immediately without doing anything
        # if the hash matches.
        upload_hash = upload_links[part_number - 1]["etag"] if "etag" in upload_links[part_number - 1] else None
        if upload_hash and repr(upload_hash) == repr(f"\"{computed_hash}\""):  # returned hash is surrounded by '"'
            return

        if not upload_links[part_number - 1]["upload_link"]:
            raise Exception(f"Invalid upload link for part {part_number}.")

        upload_link = upload_links[part_number - 1]["upload_link"]
        response = _upload_to_s3(bytes_chunk, upload_link)

        returned_hash = response.headers['ETag']
        if repr(returned_hash) != repr(f"\"{computed_hash}\""):  # The returned hash is surrounded by '"' character
            raise DataIntegrityError("The hash of the uploaded file does not match with the hash on the server.")

        self._logger.debug(f"Successfully uploaded part {part_number} for upload id {self._upload_id}")

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
        retry_count = 0
        for _ in range(self._upload_retry_count):
            try:
                _upload_to_s3(bytes_chunk, self._upload_link)
                return
            except (IOError, PartUploadError):
                self._logger.warning(f"Encountered error uploading file {self._file.name}.")
                retry_count = retry_count + 1

        if retry_count >= self._upload_retry_count:
            raise MaxRetriesExceededError(f"Max retries exceeded while uploading file {self._file.name}")


class DataIntegrityError(Exception):
    pass


class MaxRetriesExceededError(Exception):
    pass


class PartUploadError(Exception):
    pass


class S3UploadError(PartUploadError):
    pass
