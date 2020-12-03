#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sys

import jwplatform
import requests


def update_thumbnail(api_key, api_secret, video_key, position=7.0, **kwargs):
    """
    Function which updates the thumbnail for an EXISTING video utilizing position parameter.
    This function is useful for selecting a new thumbnail from with the already existing video content.
    Instead of position parameter, user may opt to utilize thumbnail_index parameter.
    Please eee documentation for further information.

    :param api_key: <string> JWPlatform api-key
    :param api_secret: <string> JWPlatform shared-secret
    :param video_key: <string> Video's object ID. Can be found within JWPlayer Dashboard.
    :param position: <float> Represents seconds into the duration of a video, for thumbnail extraction.
    :param kwargs: Arguments conforming to standards found @ https://developer.jwplayer.com/jw-platform/reference/v1/methods/videos/thumbnails/update.html
    :return: <dict> Dict which represents the JSON response.
    """
    jwplatform_client = jwplatform.v1.Client(api_key, api_secret)
    logging.info("Updating video thumbnail.")
    try:
        response = jwplatform_client.videos.thumbnails.update(
            video_key=video_key,
            position=position,  # Parameter which specifies seconds into video to extract thumbnail from.
            **kwargs)
    except jwplatform.v1.errors.JWPlatformError as e:
        logging.error("Encountered an error updating thumbnail.\n{}".format(e))
        sys.exit(e.message)
    return response


def update_thumbnail_via_upload(api_key, api_secret, video_key, local_video_image_path='', api_format='json',
                                **kwargs):
    """
    Function which updates the thumbnail for a particular video object with a locally saved image.

    :param api_key: <string> JWPlatform api-key
    :param api_secret: <string> JWPlatform shared-secret
    :param video_key: <string> Video's object ID. Can be found within JWPlayer Dashboard.
    :param local_video_image_path: <string> Local system path to an image.
    :param api_format: <string> REQUIRED Acceptable values include 'py','xml','json',and 'php'
    :param kwargs: Arguments conforming to standards found @ https://developer.jwplayer.com/jw-platform/reference/v1/methods/videos/thumbnails/update.html
    :return: <dict> Dict which represents the JSON response.
    """
    jwplatform_client = jwplatform.v1.Client(api_key, api_secret)
    logging.info("Updating video thumbnail.")
    try:
        response = jwplatform_client.videos.thumbnails.update(
            video_key=video_key,
            **kwargs)
    except jwplatform.v1.errors.JWPlatformError as e:
        logging.error("Encountered an error updating thumbnail.\n{}".format(e))
        sys.exit(e.message)
    logging.info(response)

    # Construct base url for upload
    upload_url = '{}://{}{}'.format(
        response['link']['protocol'],
        response['link']['address'],
        response['link']['path']
    )

    # Query parameters for the upload
    query_parameters = response['link']['query']
    query_parameters['api_format'] = api_format

    with open(local_video_image_path, 'rb') as f:
        files = {'file': f}
        r = requests.post(upload_url, params=query_parameters, files=files)
        logging.info('uploading file {} to url {}'.format(local_video_image_path, r.url))
        logging.info('upload response: {}'.format(r.text))
