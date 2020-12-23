import logging
from enum import Enum
from hashlib import md5
import requests
from requests import HTTPError

from jwplatform import constants, common
from jwplatform.upload_errors import DataIntegrityError, MaxRetriesExceededError


class UploadType(Enum):
    direct = "direct"
    multipart = "multipart"

class MultipartUpload:

    def __init__(self, client, upload_id: str, file, target_part_size, retry_count):
        self.upload_id = upload_id
        self.target_part_size = target_part_size
        self.upload_retry_count = retry_count
        self.file = file
        self.client = client
        self.logger = logging.getLogger(self.__class__.__name__)

    def upload(self):

        if self.target_part_size < constants.MIN_PART_SIZE:
            raise ValueError(f"The part size has to be at least greater than {constants.MIN_PART_SIZE} bytes.")

        filename = self.file.name
        file_size = common.get_file_size(self.file)
        part_count = file_size // self.target_part_size + 1

        if part_count > 1000:
            raise ValueError(f"The given file cannot be divided into more than 1000 parts. Please try increasing the "
                             f"target part size.")

        # Get the part links
        upload_links = self._get_pre_signed_part_links(part_count)

        # Upload the parts
        for part_number in range(1, part_count + 1):
            bytes_chunk = self.file.read(self.target_part_size)
            if part_number < part_count and len(bytes_chunk) != self.target_part_size:
                raise IOError("Failed to read enough bytes")
            retry_count = 0
            while retry_count < self.upload_retry_count:
                try:
                    self._upload_part(bytes_chunk, part_number, upload_links)
                    break
                except (DataIntegrityError, HTTPError):
                    self.logger.warning(f"Encountered error upload part {part_number} of {part_count} for file {filename}."
                                        f" Retrying.")
                    retry_count = retry_count + 1

            if retry_count >= self.upload_retry_count:
                raise MaxRetriesExceededError(f"Max retries ({self.upload_retry_count}) exceeded while uploading part"
                                              f" {part_number} of {part_count} for file {filename}.")

        # Mark upload as complete
        self._mark_upload_completion()

    def _upload_part(self, bytes_chunk, part_number, upload_links):
        # Add a S3 server-side checksum validation too if possible.
        computed_hash = self._compute_part_hash(bytes_chunk)

        # Check if the file has already been uploaded and the hash matches. Return immediately without doing anything
        # if the hash matches.
        upload_hash = upload_links[part_number - 1]["etag"] if "etag" in upload_links[part_number - 1] else None
        if upload_hash:
            if repr(upload_hash) == repr(f"\"{computed_hash}\""):  # The returned hash is surrounded by '"' character
                return

        upload_link = upload_links[part_number - 1]["upload_link"] if "upload_link" in upload_links[part_number - 1] \
            else None
        if not upload_link:
            raise Exception(f"Invalid upload link for part {part_number}.")

        resp = requests.put(upload_links[part_number - 1]["upload_link"], data=bytes_chunk)
        resp.raise_for_status()

        returned_hash = resp.headers['ETag']
        if repr(returned_hash) != repr(f"\"{computed_hash}\""):  # The returned hash is surrounded by '"' character
            raise DataIntegrityError("The hash of the uploaded file does not match with the hash on the server.")
        self.logger.info(f"Successfully uploaded part {part_number} for upload id {self.upload_id}")

    def _get_pre_signed_part_links(self, part_count) -> {}:
        query_params = {'page_length': part_count}

        resp = self.client.list(resource_name='uploads', resource_id=self.upload_id, subresource_name='parts',
                                query_params=query_params)

        body = resp.json_body
        # Process the results if there are multiple pages
        total_page_count = body['total'] // part_count
        parts = body['parts']
        if total_page_count > 1:
            for page_number in range(1, total_page_count):
                query_params['page'] = page_number + 1
                resp = self.client.list(resource_name='uploads', resource_id=self.upload_id, subresource_name='parts',
                                        query_params=query_params)
                body = resp.json_body
                parts.extend(body['parts'])
        return parts

    def _compute_part_hash(self, bytes_chunk) -> str:
        hashing_instance = md5()
        hashing_instance.update(bytes_chunk)
        return hashing_instance.hexdigest()

    def _mark_upload_completion(self):
        self.client.complete(self.upload_id)
        self.logger.info("Upload successful!")


class SingleUpload:

    def __init__(self, upload_link, file, retry_count):
        self.upload_link = upload_link
        self.upload_retry_count = retry_count
        self.file = file

    def upload(self):
        # Upload to S3 directly
        bytes_chunk = self.file.read()
        retry_count = 0
        while retry_count < self.upload_retry_count:
            try:
                resp = requests.put(self.upload_link, data=bytes_chunk)
                resp.raise_for_status()
                return
            except (IOError, HTTPError):
                self.logger.warning(f"Encountered error uploading file {self.file.name}.")
                retry_count = retry_count + 1

        if retry_count >= self.upload_retry_count:
            raise MaxRetriesExceededError(f"Max retries exceeded while uploading file {self.file.name}")
