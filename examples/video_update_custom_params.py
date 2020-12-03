#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sys

import jwplatform


logging.basicConfig(level=logging.INFO)


def update_custom_params(secret, site_id, media_id, params):
    """
    Function which allows you to update a video's custom params. Custom params are indicated by key-values of
    "custom.<key>" = "<value>" so they must be provided as a dictionary and passed to the platform API call.

    :param secret: <string> Secret value for your JWPlatform API key
    :param site_id: <string> ID of a JWPlatform site
    :param media_id: <string> Video's object ID. Can be found within JWPlayer Dashboard.
    :param params: Custom params in the format of a dictionary, e.g.

        >>> params = {'year': '2017', 'category': 'comedy'}
        >>> update_custom_params('XXXXXXXX', 'XXXXXXXXXXXXXXXXX', 'dfT6JSb2', params)

    :return: None
    """
    formatted_params = {'custom.{}'.format(k): v for k,v in params.items()}

    # Setup API client
    jwplatform_client = jwplatform.client.JWPlatformClient(secret)
    logging.info("Updating Video")
    try:
        response = jwplatform_client.Media.update(site_id=site_id, media_id=media_id. body={
            "metadata": {
                "custom_params": formatted_params,
            },
        })
    except jwplatform.errors.APIError as e:
        logging.error("Encountered an error updating the video\n{}".format(e))
        sys.exit(str(e))
    logging.info(response.json_body)
