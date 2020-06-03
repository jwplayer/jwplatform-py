import jwplatform
import json
import time

# update your api key and secret here
jwplatform_client = jwplatform.Client('API_KEY', 'API_SECRET')

# placeholder variable for passthrough template key
template_key = None

# grabs all the templates from your account
templates = jwplatform_client.accounts.templates.list()['templates']

# loops through all the templates and finds the passthrough template and grabs the key
for template in templates:
    if template['format']['key'] == 'passthrough':
        template_key = template['key']

# grabs total amount of videos on your account
total = jwplatform_client.videos.list()['total']

# placeholder list for all videos
all_media_ids = []

# if total is less than or equal to 1000 videos call default list with no parameters
if total <= 1000:
    videos_list = jwplatform_client.videos.list(result_limit=1000)['videos']
    all_media_ids = list(map(lambda x: x['key'], videos_list))
# else call list multiple times and append result of each call to existing list
else:
    offset = 0
    while offset < total:
        videos_list = jwplatform_client.videos.list(
            result_limit=1000, result_offset=offset)['videos']
        all_media_ids += list(map(lambda x: x['key'], videos_list))
        offset += 1000

# loops over all_media_ids list and creates a passthrough template if it does not exist
for media_id in all_media_ids:
    try:
        jwplatform_client.videos.conversions.create(
            template_key=template_key, video_key=media_id)
        print('conversion created for media id {}'.format(media_id))
        time.sleep(2)
    except Exception as e:
        print('media id: {}'.format(media_id) + str(e))
        time.sleep(2)
        continue
