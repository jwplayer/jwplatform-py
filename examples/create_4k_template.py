import jwplatform
import json

# update your api key and secret here
jwplatform_client = jwplatform.Client('APIKEY', 'APISECRET')

# comment in/out the specific width you want for your 4k transcodes
response = jwplatform_client.accounts.templates.create(
    name='4k',
    format_key='mp4',
    #width = 4096,
    width=3840,
    default=u'video',
)

print(json.dumps(response, sort_keys=True, indent=2))
