#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import sys

import jwplatform
import requests

logging.basicConfig(level=logging.INFO)


def replace_video(secret, site_id, local_video_path, media_id):
    """
    Function which allows to replace the content of an EXISTING video object.

    :param secret: <string> Secret value for your JWPlatform API key
    :param site_id: <string> ID of a JWPlatform site
    :param local_video_path: <string> Path to media on local machine.
    :param media_id: <string> Video's object ID. Can be found within JWPlayer Dashboard.
    :return:
    """
    filename = os.path.basename(local_video_path)

    # Setup API client
    jwplatform_client = jwplatform.client.JWPlatformClient(secret)
    logging.info("Updating Video")
    try:
        response = jwplatform_client.media.reupload(site_id=site_id, media_id=media_id, body={
            "upload": {
                 "method": "s3",
            },
        })
    except jwplatform.errors.APIError as e:
        logging.error("Encountered an error updating the video\n{}".format(e))
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
