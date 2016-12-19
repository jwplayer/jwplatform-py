#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sys

import jwplatform


logging.basicConfig(level=logging.INFO)


def update_video(api_key, api_secret, video_key, **kwargs):
    """
    Function which allows you to update a video

    :param api_key: <string> JWPlatform api-key
    :param api_secret: <string> JWPlatform shared-secret
    :param video_key: <string> Video's object ID. Can be found within JWPlayer Dashboard.
    :param kwargs: Arguments conforming to standards found @ https://developer.jwplayer.com/jw-platform/reference/v1/methods/videos/update.html
    :return:
    """
    # Setup API client
    jwplatform_client = jwplatform.Client(api_key, api_secret)
    logging.info("Updating Video")
    try:
        response = jwplatform_client.videos.update(
            video_key=video_key,
            **kwargs)
    except jwplatform.errors.JWPlatformError as e:
        logging.error("Encountered an error updating the video\n{}".format(e))
        sys.exit(e.message)
    logging.info(response)
