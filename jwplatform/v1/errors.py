# -*- coding: utf-8 -*-


class JWPlatformError(Exception):
    def __init__(self, message: str):
        self.message = message

    def __str__(self):
        return repr(self.message)


class JWPlatformUnknownError(JWPlatformError):
    """An Unknown Error occurred"""


class JWPlatformNotFoundError(JWPlatformError):
    """Not Found"""


class JWPlatformNoMethodError(JWPlatformError):
    """No Method Specified"""


class JWPlatformNotImplementedError(JWPlatformError):
    """Method Not Implemented"""


class JWPlatformNotSupportedError(JWPlatformError):
    """Method or parameter not supported"""


class JWPlatformCallFailedError(JWPlatformError):
    """Call Failed"""


class JWPlatformCallUnavailableError(JWPlatformError):
    """Call Unavailable"""


class JWPlatformCallInvalidError(JWPlatformError):
    """Call Invalid"""


class JWPlatformParameterMissingError(JWPlatformError):
    """Missing Parameter"""


class JWPlatformParameterEmptyError(JWPlatformError):
    """Empty Parameter"""


class JWPlatformParameterEncodingError(JWPlatformError):
    """Parameter Encoding Error"""


class JWPlatformParameterInvalidError(JWPlatformError):
    """Invalid Parameter"""


class JWPlatformPreconditionFailedError(JWPlatformError):
    """Precondition Failed"""


class JWPlatformItemAlreadyExistsError(JWPlatformError):
    """Item Already Exists"""


class JWPlatformPermissionDeniedError(JWPlatformError):
    """Permission Denied"""


class JWPlatformDatabaseError(JWPlatformError):
    """Database Error"""


class JWPlatformIntegrityError(JWPlatformError):
    """Integrity Error"""


class JWPlatformDigestMissingError(JWPlatformError):
    """Digest Missing"""


class JWPlatformDigestInvalidError(JWPlatformError):
    """Digest Invalid"""


class JWPlatformFileUploadFailedError(JWPlatformError):
    """File Upload Failed"""


class JWPlatformFileSizeMissingError(JWPlatformError):
    """File Size Missing"""


class JWPlatformFileSizeInvalidError(JWPlatformError):
    """File Size Invalid"""


class JWPlatformInternalError(JWPlatformError):
    """Internal Error"""


class JWPlatformApiKeyMissingError(JWPlatformError):
    """User Key Missing"""


class JWPlatformApiKeyInvalidError(JWPlatformError):
    """User Key Invalid"""


class JWPlatformTimestampMissingError(JWPlatformError):
    """Timestamp Missing"""


class JWPlatformTimestampInvalidError(JWPlatformError):
    """Timestamp Invalid"""


class JWPlatformTimestampExpiredError(JWPlatformError):
    """Timestamp Expired"""


class JWPlatformNonceMissingError(JWPlatformError):
    """Nonce Missing"""


class JWPlatformNonceInvalidError(JWPlatformError):
    """Nonce Invalid"""


class JWPlatformSignatureMissingError(JWPlatformError):
    """Signature Missing"""


class JWPlatformSignatureInvalidError(JWPlatformError):
    """Signature Invalid"""


class JWPlatformRateLimitExceededError(JWPlatformError):
    """Rate Limit Exceeded"""
