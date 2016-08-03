======================
JW Platform API Client
======================

A Python client library for accessing `JW Platform`_ API. Visit `JW Player Developer`_ site for more information about JW Platform API.

Installation
------------

JW Platform API library can be installed using pip:

.. code-block:: bash

  $ pip install jwplatform

Library has `Requests`_ package as dependency. It will be installed automatically when installing using ``pip``.

Usage
-----

Import ``jwplatform`` library:

.. code-block:: python

  >>> import jwplatform

Initialize ``jwplatform`` client instance (API key and secrets can be found in the JW Platform dashboard under the `account` tab):

.. code-block:: python

  >>> jwplatform_client = jwplatform.Client('API_KEY', 'API_SECRET')

Make an API request. For this example `/videos/show`_ API resource is used:

.. code-block:: python

  >>> response = jwplatform_client.videos.show(video_key='yYul4DRz')

If API request is successful, ``response`` variable will contain dictionary with information related to the response and the actual video data in ``response['video']``:

.. code-block:: python

  >>> response
  {'rate_limit': {'limit': 50, 'remaining': 47, 'reset': 1469105100},
   'status': 'ok',
   'video': {'author': None,
    'custom': {'param1': 'value 1',
     'param2': 'value 2'},
    'date': 1225962900,
    'description': None,
    'duration': '12.0',
    'error': None,
    'expires_date': 1459908560,
    'key': 'yYul4DRz',
    'link': 'http://www.jwplatform.com',
    'md5': 'b2d7312bd39cc60e9facc8ed3cbb6418',
    'mediatype': 'video',
    'size': '29478520',
    'sourceformat': None,
    'sourcetype': 'file',
    'sourceurl': None,
    'status': 'ready',
    'tags': 'new, video',
    'title': 'New test video',
    'upload_session_id': None,
    'views': 123}}

JW Platform API library will raise exception inherited from ``jwplatform.errors.JWPlatformError`` if ``response['status']`` set to ``error``. For example, there is no ``/media/show`` API resource. Requesting it will raise ``jwplatform.errors.JWPlatformNotFoundError``:

.. code-block:: python

  >>> try:
  ...     jwplatform_client.media.show()
  ... except jwplatform.errors.JWPlatformNotFoundError as err:
  ...     print(err.message)
  API method `/media/show` not found

For the complete list of available exception see `jwplatform/errors.py`_ file.

In addition to raising ``jwplatform.errors.JWPlatformError`` exceptions, JW Platform API library will
re-raise `requests.exceptions.RequestException`_ exceptions from the `Requests`_ package.

Source Code
-----------

Source code for the JW Platform API library provided on `GitHub`_.

License
-------

JW Platform API library is distributed under the `MIT license`_.

.. _`JW Platform`: https://www.jwplayer.com/products/jwplatform/
.. _`JW Player Developer`: https://developer.jwplayer.com/jw-platform/reference/v1/
.. _`/videos/show`: https://developer.jwplayer.com/jw-platform/reference/v1/methods/videos/show.html
.. _`jwplatform/errors.py`: https://github.com/jwplayer/jwplatform-py/blob/master/jwplatform/errors.py
.. _`MIT license`: https://github.com/jwplayer/jwplatform-py/blob/master/LICENSE
.. _`GitHub`: https://github.com/jwplayer/jwplatform-py
.. _`Requests`: https://pypi.python.org/pypi/requests/
.. _`requests.exceptions.RequestException`: http://docs.python-requests.org/en/master/api/#exceptions
