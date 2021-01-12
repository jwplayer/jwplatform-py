======================
JW Platform API Client
======================

A Python client library for accessing `JW Platform`_ API. Visit `JW Player Developer`_ site for more information about JW Platform API.

Installation
------------

JW Platform API library can be installed using pip:

.. code-block:: bash

  pip install jwplatform

Library has `Requests`_ package as dependency. It will be installed automatically when installing using ``pip``.

Usage
-----

Import ``jwplatform`` library:

.. code-block:: python

  from jwplatform.client import JWPlatformClient

Initialize ``jwplatform`` client instance. API keys can be created in the JW Platform dashboard on the API Credentials page. Copy the secret value to use here.

.. code-block:: python

  jwplatform_client = JWPlatformClient('API_SECRET')

Make an API request:

.. code-block:: python

  response = jwplatform_client.Media.get(site_id='SITE_ID', media_id='MEDIA_ID')

If API request is successful, ``response`` variable will contain dictionary with information related to the response and the actual video data in ``response.json_body``:

.. code-block:: python

  >>> response.json_body
  {"id": "Ny05CEfj",
   "type": "media",
   "created": "2019-09-25T15:29:11.042095+00:00",
   "last_modified": "2019-09-25T15:29:11.042095+00:00",
   "metadata": {
     "title": "Example video",
     "tags": ["new", "video"]
   }}

JW Platform API library will raise exception inherited from ``jwplatform.errors.APIError`` if anything goes wrong. For example, if there is no media with the specified media_id requesting it will raise ``jwplatform.errors.NotFoundError``:

.. code-block:: python

  try:
      jwplatform_client.Media.get(site_id='SITE_ID', media_id='BAD_MEDIA_ID')
  except jwplatform.errors.NotFoundError as err:
      print(err)

For the complete list of available exception see `jwplatform/errors.py`_ file.

Source Code
-----------

Source code for the JW Platform API library provided on `GitHub`_.

License
-------

JW Platform API library is distributed under the `MIT license`_.

.. _`JW Platform`: https://www.jwplayer.com/products/jwplatform/
.. _`JW Player Developer`: https://developer.jwplayer.com/jwplayer/reference#introduction-to-api-v2
.. _`jwplatform/errors.py`: https://github.com/jwplayer/jwplatform-py/blob/master/jwplatform/errors.py
.. _`MIT license`: https://github.com/jwplayer/jwplatform-py/blob/master/LICENSE
.. _`GitHub`: https://github.com/jwplayer/jwplatform-py
.. _`Requests`: https://pypi.python.org/pypi/requests/
