#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sys
import os
import csv
import time

import jwplatform


def make_csv(api_key, api_secret, path_to_csv=None, result_limit=1000, **kwargs):
    """
    Function which fetches a video library and writes each video_objects Metadata to CSV. Useful for CMS systems.

    :param api_key: <string> JWPlatform api-key
    :param api_secret: <string> JWPlatform shared-secret
    :param path_to_csv: <string> Local system path to desired CSV. Default will be within current working directory.
    :param result_limit: <int> Number of video results returned in response. (Suggested to leave at default of 1000)
    :param kwargs: Arguments conforming to standards found @ https://developer.jwplayer.com/jw-platform/reference/v1/methods/videos/list.html
    :return: <dict> Dict which represents the JSON response.
    """

    path_to_csv = path_to_csv or os.path.join(os.getcwd(), 'video_list.csv')
    timeout_in_seconds = 2
    max_retries = 3
    retries = 0
    offset = 0
    videos = list()

    jwplatform_client = jwplatform.Client(api_key, api_secret)
    logging.info("Querying for video list.")

    while True:
        try:
            response = jwplatform_client.videos.list(result_limit=result_limit,
                                                     result_offest=offset,
                                                     **kwargs)
        except jwplatform.errors.JWPlatformRateLimitExceededError:
            logging.error("Encountered rate limiting error. Backing off on request time.")
            if retries == max_retries:
                raise jwplatform.errors.JWPlatformRateLimitExceededError()
            timeout_in_seconds *= timeout_in_seconds  # Exponential back off for timeout in seconds. 2->4->8->etc.etc.
            retries += 1
            time.sleep(timeout_in_seconds)
            continue
        except jwplatform.errors.JWPlatformError as e:
            logging.error("Encountered an error querying for videos list.\n{}".format(e))
            raise e

        # Reset retry flow-control variables upon a non successful query (AKA not rate limited)
        retries = 0
        timeout_in_seconds = 0

        # Add all fetched video objects to our videos list.
        videos.extend(response.get('videos', []))
        last_query_total = response.get('total', 0)
        if last_query_total < result_limit:  # Condition which defines you've reached the end of the library
            break
        offset += last_query_total

    # Section for writing video library to csv
    desired_fields = ['key', 'title', 'description', 'tags', 'date', 'link']
    should_write_header = not os.path.isfile(path_to_csv)
    with open(path_to_csv, 'a+') as path_to_csv:
        # Only write columns to the csv which are specified above. Columns not specified are ignored.
        writer = csv.DictWriter(path_to_csv, fieldnames=desired_fields, extrasaction='ignore')
        if should_write_header:
            writer.writeheader()
        writer.writerows(videos)
