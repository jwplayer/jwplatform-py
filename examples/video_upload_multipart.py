#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
from jwplatform import Client
from jwplatform.errors import JWPlatformError
import logging
import os
import requests
import json
import sys
import argparse

logging.basicConfig(level=logging.INFO)

JW_API_KEY = os.environ.get('JWP_API_KEY')
JW_API_SECRET = os.environ.get('JWP_API_SECRET')


class MultipartUploader(object):
    # set default buffer size to 10 MB
    BUFFER_SIZE = 1000000

    def __init__(self, video_file_path):
        self._file_path = video_file_path
        self._file_size = os.stat(video_file_path).st_size
        self._file_name = os.path.split(video_file_path)[1]
        self._setup()

    def _setup(self):
        """
        Initializes the MultipartUploader object for use.  Namely, this method configures the upload
        URL and all relevant parameters and headers for the POST requests to be made.

        :param filename: <str> the name of the video file
        """
        try:
            self._jwplatform_client = Client(JW_API_KEY, JW_API_SECRET)
            self._response = self._jwplatform_client.videos.create(upload_method='multipart', title=self._file_name)
            self._filename = self._file_name

            self._upload_url = '{}://{}{}'.format(
                self._response['link']['protocol'],
                self._response['link']['address'],
                self._response['link']['path']
            )
            logging.info('Upload URL to be used: {}'.format(self._upload_url))
            self._query_parameters = self._response['link']['query']
            self._query_parameters['api_format'] = 'json'
            self._headers = {'X-Session-ID': self._response['session_id']}
            self._offset = 0

        except JWPlatformError as e:
            logging.exception('An error occurred during the uploader setup. Check that your API keys are properly '
                              'set up in your environment, and ensure that the video file path exists.')
            raise

    def _upload_chunk(self, chunk):
        """
        Handles the POST request needed to upload a single portion of the video file.
        Serves as a helper method for upload().

        The offset used to determine where a chunk begins and ends is updated in the course of
        this method's execution.

        :param chunk: <byte[]> the raw bytes of data from the video file
        """

        begin_chunk = self._offset
        # the last byte in the range is INCLUSIVE, hence the -1
        end_chunk = begin_chunk + len(chunk) - 1

        logging.info("begin_chunk / end_chunk = {} / {}".format(begin_chunk, end_chunk))
        self._headers.update({'X-Content-Range': 'bytes {}-{}/{}'.format(begin_chunk, end_chunk, self._file_size)})
        self._headers.update({'Content-Disposition': 'attachment; filename="{}"'.format(self._filename)})
        self._headers.update({'Content-Type': 'application/octet-stream'})
        self._headers.update({'Content-Length': str((end_chunk - begin_chunk) + 1)})

        try:
            response = requests.post(self._upload_url, params=self._query_parameters, headers=self._headers, data=chunk)
            response.raise_for_status()
        except requests.exceptions.RequestException:
            raise

        self._offset += len(chunk)

    def run(self):
        """
        Manager method for directing the upload process.  Calls _upload_chunk() repeatedly
        until the complete video file has been uploaded.
        """
        try:
            with open(self._file_path, 'rb') as file_to_upload:
                chunk = file_to_upload.read(self.BUFFER_SIZE)
                while len(chunk) > 0:
                    self._upload_chunk(chunk)
                    chunk = file_to_upload.read(self.BUFFER_SIZE)

        # catch any exceptions that bubbled up
        except requests.exceptions.RequestException as e:
            logging.exception("Error posting data, stopping upload...".format(e))
            raise

        except IOError:
            logging.exception('Could not read file to upload.')
            raise

        except Exception:
            logging.exception('An error occurred during the multipart upload process')
            raise

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--filepath', dest='filepath', type=str,
                        help='Absolute path to video file')
    arguments = parser.parse_args()
    file_path = arguments.filepath

    try:
        uploader = MultipartUploader(video_file_path=file_path)
        logging.info("Uploading {}".format(file_path))
        uploader.run()
        logging.info("Uploader finished successfully")

    except Exception:
        logging.error('Uploader failed')
