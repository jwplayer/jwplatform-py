Changelog
=========

2.0.1 (2021-01-11)
------------------

- Fix a bug on generating the signature when array value is in the query string.

2.0.0 (2020-12-03)
------------------

- Added support for JWPlatform API v2
- All existing v1 API functionality has been moved to the jwplatform.v1 submodule (from jwplatform).

1.3.0 (2019-12-22)
------------------

- remove Python 2 compatability

1.2.2 (2018-04-10)
------------------

- parameters are now included in the request body by default for POST requests

1.2.1 (2017-11-20)
------------------

- improved default parameters handling when instantiating client
- added exponential connection backoff

1.2.0 (2016-11-22)
------------------

- allow additional Request package params in API requests

1.1.0 (2016-11-03)
------------------

- added JWPlatformRateLimitExceededError exception

1.0.0 (2016-07-21)
------------------

- Initial release.
