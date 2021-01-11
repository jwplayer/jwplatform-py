import os
import logging
from jwplatform.client import JWPlatformClient
from jwplatform.upload import PartUploadError, DataIntegrityError

logging.basicConfig(level=logging.DEBUG)
JW_API_SECRET = os.environ.get('JW_API_SECRET')


def run_multipart_upload(site_id, video_file_path):
    """
    Creates a media and uploads the media file using a direct or multi-part mechanism.
    Args:
        site_id: The site ID
        video_file_path: The <str> containing the absolute path to the media file.

    Returns: None

    """
    media_client_instance = JWPlatformClient().Media
    upload_parameters = {
        'site_id': site_id,
        'target_part_size': 5 * 1024 * 1024,
        'retry_count': 3
    }
    kwargs = upload_parameters

    with open(video_file_path, "rb") as file:
        upload_context = media_client_instance.create_media_and_get_upload_context(file, **kwargs)
        media_client_instance.upload(file, upload_context, **kwargs)
        logging.info(f"Successfully uploaded file:{file.name}")


def run_multipart_upload_with_auto_resume(site_id, video_file_path, retry_count):
    """
        Creates a media and uploads the media file using a direct or multi-part mechanism.
        Args:
            site_id: The site ID
            video_file_path: The <str> containing the absolute path to the media file.
            retry_count: Number of retries to attempt before exiting.

        Returns: None

        """
    media_client_instance = JWPlatformClient().Media
    upload_parameters = {
        'site_id': site_id,
        'target_part_size': 5 * 1024 * 1024
    }
    kwargs = upload_parameters

    with open(video_file_path, "rb") as file:
        upload_context = media_client_instance.create_media_and_get_upload_context(file, **kwargs)
        try:
            media_client_instance.upload(file, upload_context, **kwargs)
            return
        except Exception as ex:
            logging.exception(ex)
            logging.debug("Resuming upload.")
        while retry_count < 10:
            try:
                media_client_instance.resume(file, upload_context, **kwargs)
                return
            except (DataIntegrityError, PartUploadError, IOError, OSError) as ex:
                retry_count = retry_count + 1
                logging.debug(f"Resuming upload again. Retry attempt:{retry_count}")
                logging.exception(ex)
