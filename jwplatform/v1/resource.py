# -*- coding: utf-8 -*-

from jwplatform.v1 import client
from jwplatform.v1 import errors


class Resource:
    """JW Platform API resource.

    Provides access to the JW Platform API resources using dot notation.

    Args:
        name (str): JW Platform API resource (sub-)name.
        client (:obj:`jwplatform.Client`): Instance of :jwplatform.Client:

    Examples:
        '/videos/tracks/show' can be called as:

        >>> track = jwplatform_client.videos.tracks.show(track_key='abcd1234')
    """

    def __init__(self, name: str, client):
        self._name = name
        self._client = client

    def __getattr__(self, resource_name):
        return Resource('.'.join((self._name, resource_name)), self._client)

    @property
    def path(self):
        """str: JW Platform API resource path.

        Path of the API resource represented by this instance,
        e.g. '/videos/tracks/show'.
        """
        return '/{}'.format(self._name.replace('.', '/'))

    def __call__(self, http_method='GET', request_params=None, use_body=None,
                 **kwargs):
        """Requests API resource method.

        Args:
            http_method (str): HTTP method. Defaults to 'GET' if not specified.

            request_params (dict): Additional parameters that requests.request
            method accepts. See Request package documentation for details:
            http://docs.python-requests.org/en/master/api/#requests.request
            Note: 'method', 'url', 'params' and 'data' keys should not be
            included in the request_params dictionary.

            use_body (bool): If True, pass parameters in the request body,
            otherwise pass parameters via the URL query string. For the POST
            methods, this defaults to True. For other methods it defaults to
            False.

            **kwargs (dict): Keyword arguments specific to the API resource method.

        Returns:
            dict: Dictionary with API resource data. If request is successful and
                  response 'status' is 'ok'.

        Raises:
            jwplatform.errors.JWPlatformError: If response 'status' is 'error'.
            requests.RequestException: :requests: packages specific exception.
        """

        _request_params = {} if request_params is None else request_params.copy()

        # Remove certain parameters from _request_params dictionary as they are
        # provided as separate arguments.
        _request_params.pop('method', None)
        _request_params.pop('url', None)
        _request_params.pop('params', None)
        _request_params.pop('data', None)

        # Whether we default to using the request body to pass parameters or not
        # depends on the method. Respect the value of use_body which was passed
        # above the default.
        use_body = use_body if use_body is not None else http_method == 'POST'

        url, params = self._client._build_request(self.path, kwargs)

        if use_body:
            _request_params['data'] = params
        else:
            _request_params['params'] = params

        response = self._client._connection.request(
            http_method, url, **_request_params)

        try:
            _response = response.json()
        except ValueError:
            raise errors.JWPlatformUnknownError(
                'Not a valid JSON string: {}'.format(response.text))
        except:
            raise

        if response.status_code != 200:
            if _response['status'] == 'error':
                try:
                    error_class = getattr(errors, 'JWPlatform{}Error'.format(
                        _response['code'].rstrip('Error')))
                except AttributeError:
                    error_class = errors.JWPlatformUnknownError
                raise error_class(_response['message'])
            else:
                errors.JWPlatformUnknownError(response.text)
        else:
            return _response
