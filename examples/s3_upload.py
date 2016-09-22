#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging

import jwplatform
import requests

logging.basicConfig(level=logging.INFO)

def upload_video(api_key, api_secret, video_file):

    # Setup API client
    jwplatform_client = jwplatform.Client(api_key, api_secret)

    # Make /videos/create API call
    logging.info("creating video")
    try:
        response = jwplatform_client.videos.create(
            title=os.path.basename(video_file),
            upload_method='s3')
    except jwplatform.errors.JWPlatformError as e:
        logging.error("Encountered an error creating a video")
        sys.exit(e.message)
    logging.info(response)

    # Construct base url for upload
    upload_url = '{}://{}{}'.format(
        response['link']['protocol'],
        response['link']['address'],
        response['link']['path']
    )

    # Query parameters for the upload
    query_parameters = response['link']['query']


    # HTTP PUT upload using requests
    with open(video_file, 'rb') as f:
        r = requests.put(upload_url, params=query_parameters, data=f)
        logging.info('uploading file {} to url {}'.format(video_file, r.url))
        logging.info('upload response: {}'.format(r.text))
        logging.info(r)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Upload a file to JW Platform.')
    parser.add_argument('api_key', type=str,
                       help='The API Key of your JW Platform account.')
    parser.add_argument('api_secret', type=str,
                       help='The API Secret of your JW Platform account.')
    parser.add_argument('video_file', type=str,
                       help='The path and file name you want to upload. ex: path/file.mp4')
    args = parser.parse_args()
    upload_video(args.api_key, args.api_secret, args.video_file)
