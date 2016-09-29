#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

import jwplatform
import requests

logging.basicConfig(level=logging.INFO)


def create_video(api_key, api_secret, local_video_path, api_format='json', **kwargs):
    """
    Function which creates new video object via multipart upload method.

    :param api_key: <string> JWPlatform api-key
    :param api_secret: <string> JWPlatform shared-secret
    :param local_video_path: <string> Path to media on local machine.
    :param api_format: <string> REQUIRED Acceptable values include 'py','xml','json',and 'php'
    :param kwargs: Arguments conforming to standards found @ https://developer.jwplayer.com/jw-platform/reference/v1/methods/videos/create.html
    :return:
    """
    # Setup API client
    jwplatform_client = jwplatform.Client(api_key, api_secret)

    # Make /videos/create API call
    logging.info("Registering new Video-Object")
    try:
        response = jwplatform_client.videos.create(upload_method='multipart', **kwargs)
    except jwplatform.errors.JWPlatformError as e:
        logging.error("Encountered an error creating a video\n{}".format(e))
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
    headers = {'X-Session-ID': response['session_id']}

    with open(local_video_path, 'rb') as f:
        files = {'file': f}
        r = requests.post(upload_url,
                          params=query_parameters,
                          headers=headers,
                          files=files)
        logging.info('uploading file {} to url {}'.format(local_video_path, r.url))
        logging.info('upload response: {}'.format(r.text))
        logging.info(r)
