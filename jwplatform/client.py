# -*- coding: utf-8 -*-
import http.client
import json
import urllib.parse

from jwplatform import __version__, constants
from jwplatform.errors import APIError
from jwplatform.response import APIResponse, ResourceResponse, ResourcesResponse
from jwplatform.upload import MultipartUpload, determine_upload_method, SingleUpload, UploadType

JWPLATFORM_API_HOST = 'api-dev.jwplayer.com'
JWPLATFORM_API_PORT = 443
USER_AGENT = f"jwplatform_client-python/{__version__}"

__all__ = (
    "JWPLATFORM_API_HOST", "JWPLATFORM_API_PORT", "USER_AGENT", "JWPlatformClient"
)


class JWPlatformClient:
    """JW Platform API client.

    An API client for the JW Platform. For the API documentation see:
    https://developer.jwplayer.com/jwplayer/reference#introduction-to-api-v2

    Args:
        secret (str): Secret value for your API key
        host (str, optional): API server host name.
                              Default is 'api.jwplayer.com'.

    Examples:
        jwplatform_client = jwplatform.client.Client('API_KEY')
    """

    def __init__(self, secret=None, host=None):
        if host is None:
            host = JWPLATFORM_API_HOST

        self._api_secret = secret
        self._connection = http.client.HTTPSConnection(
            host=host,
            port=JWPLATFORM_API_PORT
        )

        self.analytics = _AnalyticsClient(self)
        self.Import = _ImportClient(self)
        self.Channel = _ChannelClient(self)
        self.Media = _MediaClient(self)
        self.WebhookClient = _WebhookClient(self)
        self.advertising = _AdvertisingClient(self)

    def raw_request(self, method, url, body=None, headers=None):
        """
        Exposes http.client.HTTPSConnection.request without modifying the request.

        Either returns an APIResponse or raises an APIError.
        """
        if headers is None:
            headers = {}

        self._connection.request(method, url, body, headers)
        response = self._connection.getresponse()

        if response.status >= 200 and response.status <= 299:
            return APIResponse(response)

        raise APIError.from_response(response)

    def request(self, method, path, body=None, headers=None, query_params=None):
        """
        Sends a request using the client's configuration.

        Args:
            method (str): HTTP request method
            path (str): Resource or endpoint to request
            body (dict): Contents of the request body  that will be converted to JSON
            headers (dict): Any additional HTTP headers
            query_params (dict): Any additional query parameters to add to the URI
        """
        if headers is None:
            headers = {}

        if "User-Agent" not in headers:
            headers["User-Agent"] = USER_AGENT
        if "Authorization" not in headers and self._api_secret is not None:
            headers["Authorization"] = f"Bearer {self._api_secret}"
        if "Content-Type" not in headers:
            headers["Content-Type"] = "application/json"

        if body is not None:
            body = json.dumps(body)
        if query_params is not None:
            path += "?" + urllib.parse.urlencode(query_params)

        return self.raw_request(method=method, url=path, body=body, headers=headers)


class _ScopedClient:

    def __init__(self, client: JWPlatformClient):
        self._client = client


class _GenericResourceClient(_ScopedClient):
    _resource_name = None
    _id_name = None
    _collection_path = "/v2/{resource_name}/{resource_id}/{subresource_name}"
    _singular_path = "/v2/{resource_name}/{resource_id}/{subresource_name}/{subresource_id}"

    def __init__(self, client: JWPlatformClient):
        super().__init__(client)

    def list(self, resource_name, resource_id, subresource_name, query_params=None):
        response = self._client.request(
            method="GET",
            path=self._collection_path.format(resource_name=resource_name, resource_id=resource_id,
                                              subresource_name=subresource_name),
            query_params=query_params
        )
        return ResourcesResponse.from_client(response, subresource_name, self.__class__)


class _UploadClient(_GenericResourceClient):
    _collection_path = "/v1/uploads/{resource_id}/{subresource_name}"
    _singular_path = "/v1/uploads/{resource_id}/{subresource_name}/{subresource_id}"

    def __init__(self, api_secret, base_url='upload.jwplayer.com'):
        client = JWPlatformClient(secret=api_secret, host=base_url)
        super().__init__(client)

    def complete(self, resource_name, resource_id, subresource_name, body=None):
        response = self._client.request(
            method="PUT",
            path=self._collection_path.format(resource_name=resource_name, resource_id=resource_id,
                                              subresource_name=subresource_name),
            body=body
        )
        return ResourceResponse.from_client(response, self.__class__)


class _ResourceClient(_ScopedClient):
    _resource_name = None
    _id_name = None
    _collection_path = "/v2/{resource_name}/"
    _singular_path = "/v2/{resource_name}/{resource_id}/"

    def list(self, site_id, query_params=None):
        response = self._client.request(
            method="GET",
            path=self._collection_path.format(site_id=site_id, resource_name=self._resource_name),
            query_params=query_params
        )
        return ResourcesResponse.from_client(response, self._resource_name, self.__class__)

    def create(self, site_id, body=None, query_params=None):
        response = self._client.request(
            method="POST",
            path=self._collection_path.format(site_id=site_id, resource_name=self._resource_name),
            body=body,
            query_params=query_params
        )
        return ResourceResponse.from_client(response, self.__class__)

    def get(self, site_id, query_params=None, **kwargs):
        resource_id = kwargs[self._id_name]
        response = self._client.request(
            method="GET",
            path=self._singular_path.format(site_id=site_id, resource_name=self._resource_name,
                                            resource_id=resource_id),
            query_params=query_params
        )
        return ResourceResponse.from_client(response, self.__class__)

    def update(self, site_id, body, query_params=None, **kwargs):
        resource_id = kwargs[self._id_name]
        response = self._client.request(
            method="PATCH",
            path=self._singular_path.format(site_id=site_id, resource_name=self._resource_name,
                                            resource_id=resource_id),
            body=body,
            query_params=query_params
        )
        return ResourceResponse.from_client(response, self.__class__)

    def delete(self, site_id, query_params=None, **kwargs):
        resource_id = kwargs[self._id_name]
        return self._client.request(
            method="DELETE",
            path=self._singular_path.format(site_id=site_id, resource_name=self._resource_name,
                                            resource_id=resource_id),
            query_params=query_params
        )


class _SiteResourceClient(_ResourceClient):
    _collection_path = "/v2/sites/{site_id}/{resource_name}/"
    _singular_path = "/v2/sites/{site_id}/{resource_name}/{resource_id}/"


class _AnalyticsClient(_ScopedClient):

    def query(self, site_id, body, query_params=None):
        return self._client.request(
            method="POST",
            path=f"/v2/sites/{site_id}/queries/",
            body=body,
            query_params=query_params
        )


class _ImportClient(_SiteResourceClient):
    _resource_name = "imports"
    _id_name = "import_id"


class _ChannelClient(_SiteResourceClient):
    _resource_name = "channels"
    _id_name = "channel_id"

    def __init__(self, client):
        super().__init__(client)
        self.Event = _ChannelEventClient(client)


class _ChannelEventClient(_ScopedClient):

    def list(self, site_id, channel_id, query_params=None):
        response = self._client.request(
            method="GET",
            path=f"/v2/sites/{site_id}/channels/{channel_id}/events/",
            query_params=query_params
        )
        return ResourcesResponse.from_client(response, "events", self.__class__)

    def get(self, site_id, channel_id, event_id, query_params=None):
        response = self._client.request(
            method="GET",
            path=f"/v2/sites/{site_id}/channels/{channel_id}/events/{event_id}/",
            query_params=query_params
        )
        return ResourceResponse.from_client(response, self.__class__)

    def request_master(self, site_id, channel_id, event_id, query_params=None):
        return self._client.request(
            method="PUT",
            path=f"/v2/sites/{site_id}/channels/{channel_id}/events/{event_id}/request_master/",
            query_params=query_params
        )

    def clip(self, site_id, channel_id, event_id, body=None, query_params=None):
        return self._client.request(
            method="PUT",
            path=f"/v2/sites/{site_id}/channels/{channel_id}/events/{event_id}/clip/",
            body=None,
            query_params=query_params
        )


CREATE_MEDIA_PAYLOAD = {
    "upload": {
    },
    "metadata": {

    }
}


class _MediaClient(_SiteResourceClient):
    _resource_name = "media"
    _id_name = "media_id"

    def __init__(self, client: JWPlatformClient):
        super().__init__(client)

    def reupload(self, site_id, body, query_params=None, **kwargs):
        resource_id = kwargs[self._id_name]
        return self._client.request(
            method="PUT",
            path=self._singular_path.format(site_id=site_id, resource_name=self._resource_name,
                                            resource_id=resource_id) + "reupload/",
            body=body,
            query_params=query_params
        )

    def get_upload_handler(self, site_id, file, body=None, query_params=None, **kwargs):
        if not kwargs:
            kwargs = {}

        # Determine the upload type - Single or multi-part
        target_part_size = int(kwargs['target_part_size']) if 'target_part_size' in kwargs else constants.MIN_PART_SIZE
        upload_method = determine_upload_method(file, target_part_size)
        if not body:
            body = CREATE_MEDIA_PAYLOAD.copy()
        body["upload"]["method"] = upload_method

        # Create the media
        resp = self.create(site_id, body, query_params)

        # Upload the file
        upload_handler = self.process_upload(resp, upload_method, file, **kwargs)

        # Return the upload_instance to the caller so that they can resume at their own by calling the upload
        #  again
        return upload_handler

    def process_upload(self, resp, upload_method, file, **kwargs):
        base_url = kwargs['base_url'] if 'base_url' in kwargs else None
        target_part_size = int(kwargs['target_part_size']) if 'target_part_size' in kwargs else constants.MIN_PART_SIZE
        retry_count = int(kwargs['retry_count']) if 'retry_count' in kwargs else constants.RETRY_COUNT

        if upload_method == UploadType.direct.value:
            result = resp.json_body
            direct_link = result["upload_link"]
            upload_handler = SingleUpload(direct_link, file, retry_count)
        elif upload_method == UploadType.multipart.value:
            result = resp.json_body
            upload_id = result["upload_id"]
            upload_token = result["upload_token"]
            upload_client = _UploadClient(api_secret=upload_token, base_url=base_url) \
                if base_url else _UploadClient(api_secret=upload_token)
            upload_handler = MultipartUpload(upload_client, upload_id, file, target_part_size,
                                             retry_count)
        else:
            raise Exception('Invalid upload method')
        return upload_handler


class _WebhookClient(_ResourceClient):
    _resource_name = "webhooks"
    _id_name = "webhook_id"


class _VpbConfigClient(_ResourceClient):
    _resource_name = "vpb_configs"
    _id_name = "config_id"
    _collection_path = "/v2/sites/{site_id}/advertising/{resource_name}/"
    _singular_path = "/v2/sites/{site_id}/advertising/{resource_name}/{resource_id}/"


class _AdvertisingClient(_ScopedClient):

    def __init__(self, client):
        super().__init__(client)
        self.VpbConfig = _VpbConfigClient(client)

    def update_schedules_vpb_config(self, site_id, body, query_params=None):
        return self._client.request(
            method="PUT",
            path=f"/v2/sites/{site_id}/advertising/update_schedules_vpb_config/",
            body=body,
            query_params=query_params
        )
