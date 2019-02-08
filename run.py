import os
import sys


from dotenv import load_dotenv
from slackclient import SlackClient
import watson_developer_cloud

from chatbot.botclient import BotClient
from chatbot.chatbot import ChatBot


if __name__ == "__main__":
    try:
        # load environment variables
        load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
        slack_bot_id = os.environ.get("SLACK_BOT_ID")
        slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
        conversation_workspace_id = os.environ.get("CONVERSATION_WORKSPACE_ID")
        conversation_client = watson_developer_cloud.ConversationV1(
            username=os.environ.get("CONVERSATION_USERNAME"),
            password=os.environ.get("CONVERSATION_PASSWORD"),
            version='2017-05-26'
        )
        bot_client = BotClient()
        # start the chat bot
        chat_bot = ChatBot(slack_bot_id,
                           slack_client,
                           conversation_client,
                           conversation_workspace_id,
                           bot_client)
        chat_bot.start()
        sys.stdin.readline()

    except (KeyboardInterrupt, SystemExit):
        pass
    chat_bot.stop()
    chat_bot.join()
 