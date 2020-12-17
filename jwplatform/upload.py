import os
from enum import Enum
from hashlib import md5
import requests
from requests import HTTPError

from jwplatform import constants


class UploadType(Enum):
    direct = "direct"
    multipart = "multipart"


def determine_upload_method(file) -> UploadType:
    filename = file.name
    file_size = os.stat(filename).st_size
    if file_size < constants.MIN_PART_SIZE:
        return UploadType.direct.value
    return str(UploadType.multipart.value)


class MultipartUpload:

    def __init__(self, upload_id: str, upload_token: str, min_part_size, retry_count):
        self.upload_id = upload_id
        self.upload_token = upload_token
        self.base_url = 'http://upload-api.dev.longtailvideo.com'
        self.min_part_size = min_part_size
        self.upload_retry_count = retry_count

    def upload(self, file):
        # Follow the multi-part implementation
        filename = file.name
        file_size = os.stat(filename).st_size
        part_count = file_size // self.min_part_size + 1
        # Get the part links
        upload_links = self._get_pre_signed_part_links(part_count)

        # Upload the parts
        for part_number in range(1, part_count + 1):
            bytes_chunk = file.read(self.min_part_size)
            if part_number < part_count and len(bytes_chunk) != self.min_part_size:
                raise IOError("Failed to read enough bytes")
            retry_count = 0
            while retry_count < self.upload_retry_count:
                try:
                    self.upload_part(bytes_chunk, part_number, upload_links)
                    break
                except (IOError, HTTPError):
                    print(f"Encountered error upload part {part_number} of {part_count} for file {filename}.")
                    retry_count = retry_count + 1

            if retry_count >= self.upload_retry_count:
                raise IOError("Max retries exceeded while uploading part {part_number} of {part_count} for file {"
                              "filename}")

        # Mark upload as complete
        self.mark_upload_completion()

    def upload_part(self, bytes_chunk, part_number, upload_links):
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
            raise IOError("The hash of the uploaded file does not match with the hash on the server.")
        print(f"Successfully uploaded part {part_number} for upload id {self.upload_id}")

    def _get_pre_signed_part_links(self, part_count) -> {}:
        query_params = {'page_length': part_count}
        resp = requests.get(
            self.base_url
            + f"/v1/uploads/{self.upload_id}/parts",
            headers={
                "Authorization": f"Bearer {self.upload_token}",
            },
            params=query_params
        )
        resp.raise_for_status()
        body = resp.json()
        return body["parts"]

    def _compute_part_hash(self, bytes_chunk) -> str:
        hashing_instance = md5()
        hashing_instance.update(bytes_chunk)
        return hashing_instance.hexdigest()

    def mark_upload_completion(self):
        resp = requests.put(self.base_url + f"/v1/uploads/{self.upload_id}/complete",
                            headers={"Authorization": f"Bearer {self.upload_token}"})
        resp.raise_for_status()
        print("Upload successful!")


class SingleUpload:

    def __init__(self, upload_link, retry_count):
        self.upload_link = upload_link
        self.upload_retry_count = retry_count

    def upload(self, file):
        # Upload to S3 directly
        bytes_chunk = file.read()
        retry_count = 0
        while retry_count < self.upload_retry_count:
            try:
                resp = requests.put(self.upload_link, data=bytes_chunk)
                resp.raise_for_status()
                break
            except (IOError, HTTPError):
                print(f"Encountered error uploading file {file.name}.")
                retry_count = retry_count + 1

        if retry_count >= self.upload_retry_count:
            raise IOError("Max retries exceeded while uploading part {part_number} of {part_count} for file {"
                          "filename}")
