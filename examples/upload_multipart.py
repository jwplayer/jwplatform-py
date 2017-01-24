#!/usr/bin/env python

import datetime
import jwplatform
import logging
import os
import requests
import json
import sys
import argparse

logging.basicConfig(level=logging.INFO)

JW_API_KEY = os.environ.get('JW_API_KEY')
JW_API_SECRET = os.environ.get('JW_API_SECRET')


class JWPlatformBackend(object):
    NUM_PARALLEL_PROCESSES = 2
    BUFFER_SIZE = 1000000  # 10MB

    def upload_chunk(self, chunk, *args, **kwargs):
        # buffer = StringIO()
        # buffer.write(chunk)
        begin_chunk = self._offset
        end_chunk = begin_chunk + len(chunk) -1 # the last byte in the range is INCLUSIVE, hence the -1

        logging.info("begin_chunk / end_chunk = {} / {}".format(begin_chunk, end_chunk))
        self._headers.update({'X-Content-Range': 'bytes {}-{}/{}'.format(begin_chunk, end_chunk, self._size)})
        self._headers.update({'Content-Disposition': 'attachment; filename="{}"'.format(self._filename)})
        self._headers.update({'Content-Type': 'application/octet-stream'})
        self._headers.update({'Content-Length': str((end_chunk - begin_chunk) + 1)})

        try:
            r = requests.post(self._upload_url, params=self._query_parameters, headers=self._headers, data=chunk)
            r.raise_for_status()
        except requests.exceptions.RequestException as re:
            logging.exception("Error posting data, body: {}".format(re))

        self._offset += len(chunk)

    def setup(self, filename):
        self._jwplatform_client = jwplatform.Client(JW_API_KEY, JW_API_SECRET)
        self._response = self._jwplatform_client.videos.create(upload_method='multipart', title=filename)
        self._filename = filename

        self._upload_url = '{}://{}{}'.format(
            self._response['link']['protocol'],
            self._response['link']['address'],
            self._response['link']['path']
        )
        self._query_parameters = self._response['link']['query']
        self._query_parameters['api_format'] = 'json'
        self._headers = {'X-Session-ID': self._response['session_id']}
        self._offset = 0

    def upload_complete(self, request, filename):
        # Tie up loose ends, and finish the upload
        # self._pool.close()
        # self._pool.join()
        return {"data": self._response}

    def upload(self, uploaded, file_size, filename, raw_data, *args, **kwargs):
        if raw_data:
            self._size = file_size
            # File was uploaded via ajax, and is streaming in.
            chunk = uploaded.read(self.BUFFER_SIZE)
            while len(chunk) > 0:
                self.upload_chunk(chunk, *args, **kwargs)
                chunk = uploaded.read(self.BUFFER_SIZE)
        else:
            # File was uploaded via a POST, and is here.
            for chunk in uploaded.chunks():
                self.upload_chunk(chunk, *args, **kwargs)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--filepath', dest='filepath', type=str,
                        help='Absolute path to video file')
    arguments = parser.parse_args()
    file_path = arguments.filepath

    file_size = os.stat(file_path).st_size
    file_name = os.path.split(file_path)[1]

    logging.info("Uploading {}".format(file_path))
    backend = JWPlatformBackend()
    backend.setup(file_name)
    backend.upload(open(file_path, "rb"), file_size, file_name, True)
