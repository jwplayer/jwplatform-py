# -*- coding: utf-8 -*-
from collections import defaultdict

from jwplatform.response import APIResponse


class APIError(APIResponse, Exception):
    """
    Class returned when an error happens while JWPlatformClient is used to make an API request.
    """
    def __init__(self, response):
        super().__init__(response)
        self.errors = None

        if self.json_body is not None and isinstance(self.json_body, dict) and "errors" in self.json_body and isinstance(self.json_body["errors"], list):
            self.errors = self.json_body["errors"]
            self._error_code_map = defaultdict(list)

            if len(self.errors) > 0:
                for error in self.errors:
                    if isinstance(error, dict) and "code" in error and "description" in error:
                        self._error_code_map[error["code"]].append(error)

    @classmethod
    def from_response(cls, response):
        if response.status in ERROR_MAP:
            return ERROR_MAP[response.status](response)
        if response.status >= 400 and response.status <= 499:
            return ClientError(response)
        if response.status >= 500 and response.status <= 599:
            return ServerError(response)
        return UnexpectedStatusError(response)

    def has_error_code(self, code):
        if self.errors is None:
            return False
        return code in self._error_code_map

    def get_errors_by_code(self, code):
        if self.errors is None:
            return []
        return self._error_code_map[code]

    def __str__(self):
        msg = "JWPlatform API Error:\n\n"
        for error in self.errors:
            msg += "{code}: {desc}\n".format(code=error["code"], desc=error["description"])
        return msg


class ClientError(APIError):
    pass

class ServerError(APIError):
    pass

class UnexpectedStatusError(ServerError):
    pass

class InternalServerError(ServerError):
    pass

class BadGatewayError(ServerError):
    pass

class ServiceUnavailableError(ServerError):
    pass

class GatewayTimeoutError(ServerError):
    pass

class BadRequestError(ClientError):
    pass

class UnauthorizedError(ClientError):
    pass

class ForbiddenError(ClientError):
    pass

class NotFoundError(ClientError):
    pass

class MethodNotAllowedError(ClientError):
    pass

class ConflictError(ClientError):
    pass

class UnprocessableEntityError(ClientError):
    pass

class TooManyRequestsError(ClientError):
    pass


ERROR_MAP = {
    500: InternalServerError,
    502: BadGatewayError,
    503: ServiceUnavailableError,
    504: GatewayTimeoutError,
    400: BadRequestError,
    401: UnauthorizedError,
    403: ForbiddenError,
    404: NotFoundError,
    405: MethodNotAllowedError,
    409: ConflictError,
    422: UnprocessableEntityError,
    429: TooManyRequestsError,
}
