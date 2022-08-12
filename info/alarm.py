import requests
import json


def slack_message(channel, text, slack_token, slack_mode):
    if slack_mode == 'on':
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + slack_token
        }

        payload = {
            'channel': channel,
            'text': text
        }

        response = requests.post('https://slack.com/api/chat.postMessage',
                                 headers=headers,
                                 data=json.dumps(payload)
                                 )
