#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import csv
import time
import jwplatform
from jwplatform.client import JWPlatformClient

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

    jwplatform_client = JWPlatformClient(secret)
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
            csv_video['duration'] = video['duration']
            csv_video['custom_params'] = video['custom_params']
            captions = get_captions(api_client=jwplatform_client, site_id=site_id, media_id=video["id"])
            csv_video['has_captions'] = bool(len(captions))
            csv_video['captions'] = captions
            videos.append(csv_video)
        page += 1
        logging.info("Accumulated {} videos.".format(len(videos)))
        if len(next_videos) == 0:  # Condition which defines you've reached the end of the library
            break

    # Section for writing video library to csv
    desired_fields = ['id', 'title', 'description', 'tags', 'publish_start_date', 'permalink', 'custom_params', 'duration', 'has_captions', 'captions']
    should_write_header = not os.path.isfile(path_to_csv)
    with open(path_to_csv, 'a+') as path_to_csv:
        # Only write columns to the csv which are specified above. Columns not specified are ignored.
        writer = csv.DictWriter(path_to_csv, fieldnames=desired_fields, extrasaction='ignore')
        if should_write_header:
            writer.writeheader()
        writer.writerows(videos)

def get_captions(api_client, site_id, media_id):
    captions = []
    captions_response = {}
    try:
        captions_response = api_client.request(
            method='GET',
            path=f'https://api.jwplayer.com/v2/sites/{site_id}/media/{media_id}/text_tracks/'
        )
    except jwplatform.errors.TooManyRequestsError:
        logging.error("Encountered rate limiting error. Taking a 60 seconds break.")
        time.sleep(60)
        captions_response = api_client.request(
            method='GET',
            path=f'https://api.jwplayer.com/v2/sites/{site_id}/media/{media_id}/text_tracks/'
        )
    except jwplatform.errors.APIError as e:
        logging.error("Encountered an error querying for text tracks list.\n{}".format(e))
        raise e
    for text_track in captions_response.json_body['text_tracks']:
            captions.append(
                {
                    'created': text_track['created'],
                    'id': text_track['id'],
                    'metadata.label': text_track['metadata']['label'],
                    'metadata.srclang': text_track['metadata']['srclang'],
                    'status': text_track['status'],
                    'track_kind':text_track['track_kind']
                }
            )
    return captions
