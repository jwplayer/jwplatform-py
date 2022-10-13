#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sys

import jwplatform
from jwplatform.client import JWPlatformClient


logging.basicConfig(level=logging.INFO)


def update_video(secret, site_id, media_id, body):
    """
    Function which allows you to update a video

    :param secret: <string> Secret value for your JWPlatform API key
    :param site_id: <string> ID of a JWPlatform site
    :param media_id: <string> Video's object ID. Can be found within JWPlayer Dashboard.
    :param kwargs: Arguments conforming to standards found @ https://developer.jwplayer.com/jwplayer/reference#patch_v2-sites-site-id-media-media-id-
    :return:
    """
    # Setup API client
    jwplatform_client = JWPlatformClient(secret)
    logging.info("Updating Video")
    try:
        response = jwplatform_client.Media.update(site_id=site_id, media_id=media_id, body=body)
    except jwplatform.errors.APIError as e:
        logging.error("Encountered an error updating the video\n{}".format(e))
        sys.exit(str(e))
    logging.info(response.json_body)
