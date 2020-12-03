#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sys

import jwplatform


def insert_into_channel(api_key, api_secret, channel_key, video_key, **kwargs):
    """
    Function which inserts video into a channel/playlist.

    :param api_key: <string> JWPlatform api-key
    :param api_secret: <string> JWPlatform shared-secret
    :param channel_key: <string> Key of the channel to which add a video.
    :param video_key: <string> Key of the video that should be added to the channel.
    :param kwargs: Arguments conforming to standards found @ https://developer.jwplayer.com/jw-platform/reference/v1/methods/videos/create.html
    :return: <dict> Dict which represents the JSON response.
    """
    jwplatform_client = jwplatform.v1.Client(api_key, api_secret)
    logging.info("Inserting video into channel")
    try:
        response = jwplatform_client.channels.videos.create(
            channel_key=channel_key,
            video_key=video_key,
            **kwargs)
    except jwplatform.v1.errors.JWPlatformError as e:
        logging.error("Encountered an error inserting {} into channel {}.\n{}".format(video_key, channel_key, e))
        sys.exit(e.message)
    return response
