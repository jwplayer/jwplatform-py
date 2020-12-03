# -*- coding: utf-8 -*-
import json


class APIResponse:
    """
    Class returned when JWPlatformClient is used to make an API request.
    """
    def __init__(self, response):
        self.response = response
        self.status = response.status
        self.body = None
        self.json_body = None

        body = response.read()

        if body and len(body) > 0:
            self.body = body

            try:
                self.json_body = json.loads(self.body.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass

    @classmethod
    def from_copy(cls, original_response):
        copy_response = cls(original_response.response)
        copy_response.body = original_response.body
        copy_response.json_body = original_response.json_body
        return copy_response


class ResourceResponse(APIResponse):

    @classmethod
    def from_client(cls, response, resource_class):
        class ClientResponse(cls, resource_class):
            pass
        return ClientResponse.from_copy(response)


class ResourcesResponse(APIResponse):

    _resources = []

    def __iter__(self):
        return self._resources.__iter__()

    def __len__(self):
        return self._resources.__len__()

    @classmethod
    def from_client(cls, response, resource_name, resource_class):
        class ClientResponse(cls, resource_class):
            pass
        client_response = ClientResponse.from_copy(response)
        client_response._resources = client_response.json_body[resource_name]
        return client_response
