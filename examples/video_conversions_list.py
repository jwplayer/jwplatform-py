#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sys

import jwplatform


def list_conversions(api_key, api_secret, video_key, **kwargs):
    """
    Function which retrieves a list of a video object's conversions.

    :param api_key: <string> JWPlatform api-key
    :param api_secret: <string> JWPlatform shared-secret
    :param video_key: <string> Video's object ID. Can be found within JWPlayer Dashboard.
    :param kwargs: Arguments conforming to standards found @ https://developer.jwplayer.com/jw-platform/reference/v1/methods/videos/conversions/list.html
    :return: <dict> Dict which represents the JSON response.
    """
    jwplatform_client = jwplatform.v1.Client(api_key, api_secret)
    logging.info("Querying for video conversions.")
    try:
        response = jwplatform_client.videos.conversions.list(video_key=video_key, **kwargs)
    except jwplatform.v1.errors.JWPlatformError as e:
        logging.error("Encountered an error querying for video conversions.\n{}".format(e))
        sys.exit(e.message)
    return response
