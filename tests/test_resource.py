# -*- coding: utf-8 -*-

import re
import pytest
import jwplatform
import responses


@responses.activate
def test_existing_resource():
    url_expr = re.compile(r'https?://api\.test\.tst/v1/videos/show\?.*'
                          '&video_key=VideoKey.*')
    responses.add(
        responses.GET, url_expr,
        status=200,
        content_type='application/json',
        body='{"status": "ok", '
             '"rate_limit": {"reset": 1478929300, "limit": 50, "remaining": 47},'
             '"video": {"status": "ready", "expires_date": null, "description": null, '
             '"title": "Title", "views": 179, "tags": "", "sourceformat": null, '
             '"mediatype": "video", "upload_session_id": null, "custom": {}, '
             '"duration": "817.56", "sourceurl": null, "link": null, "author": null, '
             '"key": "VideoKey", "error": null, "date": 1464754765, '
             '"md5": "653bc15b6cba7319c2df9b5cf869b5b8", "sourcetype": "file", '
             '"size": "904237686"}}')

    jwp_client = jwplatform.Client('api_key', 'api_secret', host='api.test.tst')
    resp = jwp_client.videos.show(video_key='VideoKey')

    assert resp['status'] == 'ok'
    assert 'status' in resp['video']
    assert resp['video']['key'] == 'VideoKey'


@responses.activate
def test_long_resource():
    url_expr = re.compile(r'https?://api\.test\.tst/v1/a/b/c/d/f/e\?.*'
                          '&abcde=.*')
    responses.add(
        responses.GET, url_expr,
        status=200,
        content_type='application/json',
        body='{"status": "ok"}')

    jwp_client = jwplatform.Client('api_key', 'api_secret', host='api.test.tst')
    resp = jwp_client.a.b.c.d.f.e(abcde='')

    assert resp['status'] == 'ok'


@responses.activate
def test_nonexisting_resource():
    url_expr = re.compile(r'https?://api\.test\.tst/v1/videos/abcd/show\?.*'
                          '&abcd_key=AbcdKey.*')
    responses.add(
        responses.GET, url_expr,
        status=404,
        content_type='application/json',
        body='{"status": "error", '
             '"message": "API method `/videos/abcd/show` not found", '
             '"code": "NotFound", "title": "Not Found"}')

    jwp_client = jwplatform.Client('api_key', 'api_secret', host='api.test.tst')

    with pytest.raises(jwplatform.errors.JWPlatformNotFoundError) as err:
        jwp_client.videos.abcd.show(abcd_key='AbcdKey')

    assert err.value.message == 'API method `/videos/abcd/show` not found'


@responses.activate
def test_long_resource():
    url_expr = re.compile(r'https?://api\.test\.tst/v1/json/error\?.*')
    responses.add(
        responses.GET, url_expr,
        status=200,
        content_type='application/json',
        body='({"json": "error"})')

    jwp_client = jwplatform.Client('api_key', 'api_secret', host='api.test.tst')

    with pytest.raises(jwplatform.errors.JWPlatformUnknownError) as err:
        jwp_client.json.error()

    assert err.value.message == 'Not a valid JSON string: ({"json": "error"})'


@responses.activate
def test_post_existing_resource():
    url_expr = re.compile(r'https?://api\.test\.tst/v1/a/b/c/d')
    responses.add(
        responses.POST, url_expr,
        status=200,
        content_type='application/json',
        body='{"status": "ok"}')

    jwp_client = jwplatform.Client('api_key', 'api_secret', host='api.test.tst')
    resp = jwp_client.a.b.c.d(http_method='POST', abcde=123)

    assert resp['status'] == 'ok'
