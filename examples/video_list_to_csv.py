#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sys
import os
import csv
import time
import math

import jwplatform


def make_csv(secret, site_id, path_to_csv=None, result_limit=1000, query_params=None):
    """
    Function which fetches a video library and writes each video_objects Metadata to CSV. Useful for CMS systems.

    :param secret: <string> Secret value for your JWPlatform API key
    :param site_id: <string> ID of a JWPlatform site
    :param path_to_csv: <string> Local system path to desired CSV. Default will be within current working directory.
    :param result_limit: <int> Number of video results returned in response. (Suggested to leave at default of 1000)
    :param query_params: Arguments conforming to standards found @ https://developer.jwplayer.com/jwplayer/reference#get_v2-sites-site-id-media
    :return: <dict> Dict which represents the JSON response.
    """

    path_to_csv = path_to_csv or os.path.join(os.getcwd(), 'video_list.csv')
    timeout_in_seconds = 2
    max_retries = 3
    retries = 0
    page = 1
    videos = list()
    if query_params is None:
        query_params = {}
    query_params["page_length"] = result_limit

    jwplatform_client = jwplatform.client.JWPlatformClient(secret)
    logging.info("Querying for video list.")

    while True:
        try:
            query_params["page"] = page
            response = jwplatform_client.Media.list(site_id=site_id, query_params=query_params)
        except jwplatform.errors.TooManyRequestsError:
            logging.error("Encountered rate limiting error. Backing off on request time.")
            if retries == max_retries:
                raise
            timeout_in_seconds *= timeout_in_seconds  # Exponential back off for timeout in seconds. 2->4->8->etc.etc.
            retries += 1
            time.sleep(timeout_in_seconds)
            continue
        except jwplatform.errors.APIError as e:
            logging.error("Encountered an error querying for videos list.\n{}".format(e))
            raise e

        # Reset retry flow-control variables upon a non successful query (AKA not rate limited)
        retries = 0
        timeout_in_seconds = 2

        # Add all fetched video objects to our videos list.
        next_videos = response.json_body["media"]
        for video in next_videos:
            csv_video = video["metadata"]
            csv_video["id"] = video["id"]
            videos.append(csv_video)
        page += 1
        logging.info("Accumulated {} videos.".format(len(videos)))
        if len(next_videos) == 0:  # Condition which defines you've reached the end of the library
            break

    # Section for writing video library to csv
    desired_fields = ['id', 'title', 'description', 'tags', 'publish_start_date', 'permalink']
    should_write_header = not os.path.isfile(path_to_csv)
    with open(path_to_csv, 'a+') as path_to_csv:
        # Only write columns to the csv which are specified above. Columns not specified are ignored.
        writer = csv.DictWriter(path_to_csv, fieldnames=desired_fields, extrasaction='ignore')
        if should_write_header:
            writer.writeheader()
        writer.writerows(videos)
