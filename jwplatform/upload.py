import logging
import os
from enum import Enum
from hashlib import md5
import requests
from requests import HTTPError


MIN_PART_SIZE = 5 * 1024 * 1024


class UploadType(Enum):
    direct = "direct"
    multipart = "multipart"


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
        upload_links = self._get_pre_signed_part_links(part_count)

        # Upload the parts
        for part_number in range(1, part_count + 1):
            bytes_chunk = self._file.read(self._target_part_size)
            if part_number < part_count and len(bytes_chunk) != self._target_part_size:
                raise IOError("Failed to read enough bytes")
            retry_count = 0
            for _ in range(self._upload_retry_count):
                try:
                    self._upload_part(bytes_chunk, part_number, upload_links)
                    break
                except (DataIntegrityError, HTTPError) as err:
                    self._logger.warning(err)
                    if retry_count >= self._upload_retry_count:
                        raise MaxRetriesExceededError(
                            f"Max retries ({self._upload_retry_count}) exceeded while uploading part"
                            f" {part_number} of {part_count} for file {filename}.")
                    self._logger.warning(f"Encountered error upload part {part_number} of {part_count} for file "
                                         f"{filename}. Retrying.")
                    retry_count = retry_count + 1

        # Mark upload as complete
        self._mark_upload_completion()

    def _get_pre_signed_part_links(self, part_count) -> {}:
        max_page_size = 1000
        total_page_count = part_count // max_page_size + 1
        parts = []
        if total_page_count > 0:
            for page_number in range(1, total_page_count + 1):
                query_params = {'page_length': max_page_size, 'page': page_number}
                resp = self._client.list(resource_name='uploads', resource_id=self._upload_id, subresource_name='parts',
                                         query_params=query_params)
                body = resp.json_body
                parts.extend(body['parts'])
        return parts

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
        resp = requests.put(upload_link, data=bytes_chunk)
        resp.raise_for_status()

        returned_hash = resp.headers['ETag']
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
        while retry_count < self._upload_retry_count:
            try:
                resp = requests.put(self._upload_link, data=bytes_chunk)
                resp.raise_for_status()
                return
            except (IOError, HTTPError):
                self._logger.warning(f"Encountered error uploading file {self._file.name}.")
                retry_count = retry_count + 1

        if retry_count >= self._upload_retry_count:
            raise MaxRetriesExceededError(f"Max retries exceeded while uploading file {self._file.name}")


class DataIntegrityError(Exception):
    pass


class MaxRetriesExceededError(Exception):
    pass
