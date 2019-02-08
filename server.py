import deployment_tracker
import os


from dotenv import load_dotenv
from slackclient import SlackClient
import watson_developer_cloud 

from chatbot.botclient import BotClient
from chatbot.chatbot import ChatBot


try:
    from SimpleHTTPServer import SimpleHTTPRequestHandler as Handler
    from SocketServer import TCPServer as Server
except ImportError:
    from http.server import SimpleHTTPRequestHandler as Handler
    from http.server import HTTPServer as Server

# Read port selected by the cloud for our application
PORT = int(os.getenv('PORT', 8000))
# Change current directory to avoid exposure of control files
os.chdir('public')

httpd = Server(("", PORT), Handler)
try:
    # track deployment
    deployment_tracker.track()
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
    # start the souschef bot
    chat_bot = ChatBot(slack_bot_id,
                        slack_client,
                        conversation_client,
                        conversation_workspace_id,
                        bot_client)
    chat_bot.start()
    # start the http server
    print("Start serving at port %i" % PORT)
    httpd.serve_forever()
except (KeyboardInterrupt, SystemExit):
    pass
chat_bot.stop()
chat_bot.join()
httpd.server_close()
