# -*- coding: utf-8 -*-
import http.client
import logging
import json
import os
import urllib.parse
from neterr import StrictHTTPErrors

from jwplatform.version import __version__
from jwplatform.errors import APIError
from jwplatform.response import APIResponse, ResourceResponse, ResourcesResponse
from jwplatform.upload import MultipartUpload, SingleUpload, UploadType, MIN_PART_SIZE, MaxRetriesExceededError, \
    UPLOAD_BASE_URL, UploadContext, MAX_FILE_SIZE

JWPLATFORM_API_HOST = 'api.jwplayer.com'
JWPLATFORM_API_PORT = 443
USER_AGENT = f"jwplatform_client-python/{__version__}"
UPLOAD_RETRY_ATTEMPTS = 3

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

        self._logger = logging.getLogger(self.__class__.__name__)
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

        if 200 <= response.status <= 299:
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

    def request_with_retry(self, method, path, body=None, headers=None, query_params=None,
                           retry_attempts=3):
        """
        Sends a request using the client's configuration.

        Args:
            method (str): HTTP request method
            path (str): Resource or endpoint to request
            body (dict): Contents of the request body  that will be converted to JSON
            headers (dict): Any additional HTTP headers
            query_params (dict): Any additional query parameters to add to the URI
            retry_attempts: The number of retry attempts that should be made for the request.
        """
        retry_count = 0
        for _ in range(retry_attempts):
            try:
                response = self.request(method, path, body=body, headers=headers, query_params=query_params)
                return response
            except StrictHTTPErrors as http_error:
                self._logger.warning(http_error, exc_info=True)
                retry_count = retry_count + 1
                if retry_count >= retry_attempts:
                    self._logger.error(f"Exceeded maximum number of retries {retry_attempts}"
                                       f"while connecting to the host.")
                    raise


class _ScopedClient:

    def __init__(self, client: JWPlatformClient):
        self._client = client


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
    _logger = logging.getLogger(__name__)

    def reupload(self, site_id, body, query_params=None, **kwargs):
        resource_id = kwargs[self._id_name]
        return self._client.request(
            method="PUT",
            path=self._singular_path.format(site_id=site_id, resource_name=self._resource_name,
                                            resource_id=resource_id) + "reupload/",
            body=body,
            query_params=query_params
        )

    def _determine_upload_method(self, file, target_part_size) -> str:
        file_size = os.stat(file.name).st_size
        if file_size > MAX_FILE_SIZE:
            raise NotImplementedError('File size greater than 25 GB is not supported.')
        if file_size <= target_part_size:
            return UploadType.direct.value
        return UploadType.multipart.value

    def create_media_and_get_upload_context(self, file, body=None, query_params=None, **kwargs) -> UploadContext:
        """
        Creates the media and retrieve the upload context
        Args:
            file: The file-like object to the actual media file to be uploaded
            body: The body of the payload.
            query_params: The query parameters.
            **kwargs: The upload arguments.

        Returns: The UploadContext that can be reused to resuming an upload.

        """
        if not kwargs:
            kwargs = {}
        site_id = kwargs['site_id']
        # Determine the upload type - Single or multi-part
        target_part_size = int(kwargs.get('target_part_size', MIN_PART_SIZE))
        upload_method = self._determine_upload_method(file, target_part_size)
        if not body:
            body = CREATE_MEDIA_PAYLOAD.copy()

        if 'upload' not in body:
            body['upload'] = {}

        if not isinstance(body['upload'], dict):
            raise ValueError("Invalid payload structure. The upload element needs to be dictionary.")

        body["upload"]["method"] = upload_method

        # Create the media
        resp = self.create(site_id, body, query_params)

        result = resp.json_body
        upload_id = result.get("upload_id")
        upload_token = result.get("upload_token")
        direct_link = result.get("upload_link")

        upload_context = UploadContext(upload_method, upload_id, upload_token, direct_link)
        return upload_context

    def upload(self, file, upload_context: UploadContext, **kwargs) -> None:
        """
        Uploads the media file.
        Args:
            file: The file-like object to the actual media file to be uploaded
            upload_context: The query parameters.
            **kwargs: The upload parameters.

        Returns: None

        """
        upload_handler = self._get_upload_handler_for_upload_type(upload_context, file, **kwargs)
        try:
            upload_handler.upload()
        except Exception:
            file.seek(0, 0)
            raise

    def resume(self, file, upload_context: UploadContext, **kwargs) -> None:
        """
        Resumes the upload of the media file.
        Args:
            file: The file-like object to the actual media file to be resumed
            upload_context: The query parameters.
            **kwargs: The upload parameters.

        Returns: None
        """
        if not upload_context:
            raise ValueError("The provided context is None. Cannot resume the upload.")
        if not upload_context.can_resume():
            upload_context = self.create_media_and_get_upload_context(file, **kwargs)
        upload_handler = self._get_upload_handler_for_upload_type(upload_context, file, **kwargs)
        try:
            upload_handler.upload()
        except Exception:
            file.seek(0, 0)
            raise


    def _get_upload_handler_for_upload_type(self, context: UploadContext, file, **kwargs):
        upload_method = context.upload_method
        base_url = kwargs.get('base_url', UPLOAD_BASE_URL)
        target_part_size = int(kwargs.get('target_part_size', MIN_PART_SIZE))
        retry_count = int(kwargs.get('retry_count', UPLOAD_RETRY_ATTEMPTS))

        if upload_method == UploadType.direct.value:
            direct_link = context.direct_link
            upload_handler = SingleUpload(direct_link, file, retry_count, context)
        else:
            upload_token = context.upload_token
            upload_client = _UploadClient(api_secret=upload_token, base_url=base_url)
            upload_handler = MultipartUpload(upload_client, file, target_part_size,
                                             retry_count, context)
        return upload_handler


class _UploadClient(_ScopedClient):
    _collection_path = "/v1/uploads/{resource_id}"

    def __init__(self, api_secret, base_url):
        if base_url is None:
            base_url = UPLOAD_BASE_URL
        client = JWPlatformClient(secret=api_secret, host=base_url)
        super().__init__(client)

    def list(self, upload_id, query_params=None):
        """
        Lists the parts for a given multi-part upload.
        Args:
            upload_id: The upload ID for the upload
            query_params: The query parameters.

        Returns: None

        """
        resource_path = self._collection_path.format(resource_id=upload_id)
        resource_path = f"{resource_path}/parts"
        response = self._client.request_with_retry(method="GET", path=resource_path, query_params=query_params)
        return ResourcesResponse.from_client(response, 'parts', self.__class__)

    def complete(self, upload_id, body=None) -> None:
        """
        Marks the upload as complete.
        Args:
            upload_id: The upload ID for the upload
            body: [Optional] - The body of the payload.

        Returns: List of parts with their upload metadata in a JSON format.

        """
        resource_path = self._collection_path.format(resource_id=upload_id)
        resource_path = f"{resource_path}/complete"
        self._client.request_with_retry(method="PUT", path=resource_path, body=body)


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
