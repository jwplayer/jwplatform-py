#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import requests

from jwplatform.v1 import Client
from jwplatform.v1.errors import JWPlatformError


logging.basicConfig(level=logging.INFO)

JW_API_KEY = os.environ.get('JW_API_KEY')
JW_API_SECRET = os.environ.get('JW_API_SECRET')

BYTES_TO_BUFFER = 10000000


def run_upload(video_file_path):
    """
    Configures all of the needed upload_parameters and sets up all information pertinent
    to the video to be uploaded.

    :param video_file_path: <str> the absolute path to the video file
    """

    upload_parameters = {
        'file_path': video_file_path,
        'file_size': os.stat(video_file_path).st_size,
        'file_name': os.path.basename(video_file_path)
    }

    try:
        # Setup API client
        jwplatform_client = Client(JW_API_KEY, JW_API_SECRET)

        # Make /videos/create API call with multipart parameter specified
        jwplatform_video_create_response = jwplatform_client.videos.create(
            upload_method='multipart',
            title=upload_parameters['file_name']
        )

    except JWPlatformError:
        logging.exception('An error occurred during the uploader setup. Check that your API keys are properly '
                          'set up in your environment, and ensure that the video file path exists.')
        return

    # Construct base url for upload
    upload_parameters['upload_url'] = '{protocol}://{address}{path}'.format(**jwplatform_video_create_response['link'])

    logging.info('Upload URL to be used: {}'.format(upload_parameters['upload_url']))

    upload_parameters['query_parameters'] = jwplatform_video_create_response['link']['query']
    upload_parameters['query_parameters']['api_format'] = 'json'
    upload_parameters['headers'] = {'X-Session-ID': jwplatform_video_create_response['session_id']}
    # The chunk offset will be updated several times during the course of the upload
    upload_parameters['chunk_offset'] = 0

    # Perform the multipart upload
    with open(upload_parameters['file_path'], 'rb') as file_to_upload:
        while True:
            chunk = file_to_upload.read(BYTES_TO_BUFFER)
            if len(chunk) <= 0:
                break

            try:
                upload_chunk(chunk, upload_parameters)

            # Log any exceptions that bubbled up
            except requests.exceptions.RequestException:
                logging.exception('Error posting data, stopping upload...')
                break


def upload_chunk(chunk, upload_parameters):
    """
    Handles the POST request needed to upload a single portion of the video file.
    Serves as a helper method for upload_by_multipart().
    The offset used to determine where a chunk begins and ends is updated in the course of
    this method's execution.

    :param chunk: <byte[]> the raw bytes of data from the video file
    :param upload_parameters: <dict> a collection of all pieces of info needed to upload the video
    """
    begin_chunk = upload_parameters['chunk_offset']

    # The next chunk will begin at (begin_chunk + len(chunk)), so the -1 ensures that the ranges do not overlap
    end_chunk = begin_chunk + len(chunk) - 1
    file_size = upload_parameters['file_size']
    filename = upload_parameters['file_size']
    logging.info("begin_chunk / end_chunk = {} / {}".format(begin_chunk, end_chunk))

    upload_parameters['headers'].update(
        {
            'X-Content-Range': 'bytes {}-{}/{}'.format(begin_chunk, end_chunk, file_size),
            'Content-Disposition': 'attachment; filename="{}"'.format(filename),
            'Content-Type': 'application/octet-stream',
            'Content-Length': str((end_chunk - begin_chunk) + 1)
        }
    )

    response = requests.post(
        upload_parameters['upload_url'],
        params=upload_parameters['query_parameters'],
        headers=upload_parameters['headers'],
        data=chunk
    )
    response.raise_for_status()

    # As noted before, the next chunk begins at (begin_chunk + len(chunk))
    upload_parameters['chunk_offset'] = begin_chunk + len(chunk)
