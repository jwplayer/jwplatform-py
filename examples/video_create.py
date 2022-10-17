#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import sys

import jwplatform
from jwplatform.client import JWPlatformClient
import requests

logging.basicConfig(level=logging.INFO)


def create_video(secret, site_id, local_video_path, body=None):
    """
    Function which creates new video object via direct upload method.

    :param secret: <string> Secret value for your JWPlatform API key
    :param site_id: <string> ID of a JWPlatform site
    :param local_video_path: <string> Path to media on local machine.
    :param body: Arguments conforming to standards found @ https://developer.jwplayer.com/jwplayer/reference#post_v2-sites-site-id-media
    :return:
    """
    filename = os.path.basename(local_video_path)
    if body is None:
        body = {}
    body["upload"] = {
        "method": "direct",
    }

    # Setup API client
    jwplatform_client = JWPlatformClient(secret)

    # Make /videos/create API call
    logging.info("creating video")
    try:
        response = jwplatform_client.Media.create(site_id=site_id, body=body)
    except jwplatform.errors.APIError as e:
        logging.error("Encountered an error creating a video\n{}".format(e))
        sys.exit(str(e))
    logging.info(response.json_body)

    # HTTP PUT upload using requests
    upload_url = response.json_body["upload_link"]
    headers = {'Content-Disposition': 'attachment; filename="{}"'.format(filename)}
    with open(local_video_path, 'rb') as f:
        r = requests.put(upload_url, headers=headers, data=f)
        logging.info('uploading file {} to url {}'.format(local_video_path, r.url))
        logging.info('upload response: {}'.format(r.text))
        logging.info(r)
