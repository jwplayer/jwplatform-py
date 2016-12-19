#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sys

import jwplatform


logging.basicConfig(level=logging.INFO)


def update_custom_params(api_key, api_secret, video_key, params):
    """
    Function which allows you to update a video's custom params. Custom params are indicated by key-values of
    "custom.<key>" = "<value>" so they must be provided as a dictionary and passed to the platform API call.

    :param api_key: <string> JWPlatform api-key
    :param api_secret: <string> JWPlatform shared-secret
    :param video_key: <string> Video's object ID. Can be found within JWPlayer Dashboard.
    :param params: Custom params in the format of a dictionary, e.g.

        >>> params = {'year': '2017', 'category': 'comedy'}
        >>> update_custom_params('XXXXXXXX', 'XXXXXXXXXXXXXXXXX', 'dfT6JSb2', params)

    :return: None
    """
    formatted_params = {'custom.{}'.format(k): v for k,v in params.items()}

    # Setup API client
    jwplatform_client = jwplatform.Client(api_key, api_secret)
    logging.info("Updating Video")
    try:
        response = jwplatform_client.videos.update(
            video_key=video_key,
            **formatted_params)
    except jwplatform.errors.JWPlatformError as e:
        logging.error("Encountered an error updating the video\n{}".format(e))
        sys.exit(e.message)
    logging.info(response)
