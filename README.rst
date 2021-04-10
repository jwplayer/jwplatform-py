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

List calls allow for (optional) querying and filtering. This can be done by passing the query parameters as a dict to the `query_params` keyword argument on list calls:

.. code-block:: python

  response = jwplatform_client.Media.list(
    site_id="SITE_ID",
    query_params={
        "page": 1,
        "page_length": 10,
        "sort": "title:asc",
        "q": "external_id: abcdefgh",
    },
  )

All query parameters are optional. `page`, `page_length`, and `sort` parameters default to 1, 10, and "created:dsc", respectively. The `q` parameter allows for filtering on different
attributes and may allow for AND/OR querying depending on the resource. For full documentation on the query syntax and endpoint specific details please refer to developer.jwplayer.com.


Source Code
-----------

Source code for the JW Platform API library provided on `GitHub`_.

V1 Client
---------

The V1 Client remains available for use, but is deprecated. We strongly recommend using the V2 Client when possible.

To use the V1 Client, import the Client from the `v1` namespace.

.. code-block:: python

  import jwplatform.v1

  api_client = jwplatform.v1.Client('SITE_ID', 'V1_API_SECRET')

License
-------

JW Platform API library is distributed under the `MIT license`_.

.. _`JW Platform`: https://www.jwplayer.com/products/jwplatform/
.. _`JW Player Developer`: https://developer.jwplayer.com/jwplayer/reference#introduction-to-api-v2
.. _`jwplatform/errors.py`: https://github.com/jwplayer/jwplatform-py/blob/master/jwplatform/errors.py
.. _`MIT license`: https://github.com/jwplayer/jwplatform-py/blob/master/LICENSE
.. _`GitHub`: https://github.com/jwplayer/jwplatform-py
.. _`Requests`: https://pypi.python.org/pypi/requests/
