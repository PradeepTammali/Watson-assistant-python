import os
from slackclient import SlackClient
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

BOT_NAME = 'chatbot'
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

if __name__ == "__main__":
  api_call = slack_client.api_call("users.list")
  if api_call.get('ok'):
    # retrieve all users so we can find our bot
    users = api_call.get('members')
    for user in users:
      if 'name' in user and user.get('name') == BOT_NAME:
        print("Bot ID for '" + user['name'] + "' is " + user.get('id'))
  else:
    print("could not find bot user with the name " + BOT_NAME)
