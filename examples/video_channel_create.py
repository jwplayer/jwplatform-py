#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sys

import jwplatform


def create_channel(api_key, api_secret, channel_type='manual', **kwargs):
    """
    Function which creates a new channel. Channels serve as containers of video/media objects.

    :param api_key: <string> JWPlatform api-key
    :param api_secret: <string> JWPlatform shared-secret
    :param channel_type: <string> REQUIRED Acceptable values include 'manual','dynamic','trending','feed','search'
    :param kwargs: Arguments conforming to standards found @ https://developer.jwplayer.com/jw-platform/reference/v1/methods/channels/create.html
    :return: <dict> Dict which represents the JSON response.
    """
    jwplatform_client = jwplatform.v1.Client(api_key, api_secret)
    logging.info("Creating new channel with keyword args.")
    try:
        response = jwplatform_client.channels.create(type=channel_type, **kwargs)
    except jwplatform.v1.errors.JWPlatformError as e:
        logging.error("Encountered an error creating new channel.\n{}".format(e))
        sys.exit(e.message)
    return response
