import pprint
import sys
import time
import threading
import pycountry
from .user_state import UserState


class ChatBot(threading.Thread):

    def __init__(self, slack_bot_id, slack_client, conversation_client, conversation_workspace_id, bot_client):
        threading.Thread.__init__(self)
        self.running = True
        self.slack_bot_id = slack_bot_id
        self.slack_client = slack_client
        self.conversation_client = conversation_client
        self.conversation_workspace_id = conversation_workspace_id
        self.bot_client = bot_client
        
        self.at_bot = "<@" + slack_bot_id + ">:"
        self.delay = 0.5  # second
        self.user_state_map = {}
        self.pp = pprint.PrettyPrinter(indent=4)

    def parse_slack_output(self, slack_rtm_output):
        output_list = slack_rtm_output
        if output_list and len(output_list) > 0:
            for output in output_list:
                if output and 'text' in output and 'user_profile' not in output and self.at_bot in output['text']:
                    return output['text'].split(self.at_bot)[1].strip().lower(), output['user'], output['channel']
                elif output and 'text' in output and 'user_profile' not in output:
                    return output['text'].lower(), output['user'], output['channel']
        return None, None, None

    def post_to_slack(self, response, channel):
        self.slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True)

    def handle_message(self, message, message_sender, channel):
        try:
            # get or create state for the user
            if message_sender in self.user_state_map.keys():
                state = self.user_state_map[message_sender]
            else:
                state = UserState(message_sender)
                self.user_state_map[message_sender] = state
            # send message to watson conversationv
            watson_response = self.conversation_client.message(
                workspace_id=self.conversation_workspace_id,
                message_input={'text': message},
                context=state.conversation_context)
            # update conversation context
            state.conversation_context = watson_response['context']
            # route response
            if state.conversation_context['response'] and state.conversation_context['response']['intent_po_status'] == 'true':
                response = self.get_po_status(state, watson_response['output']['text'][0])
            elif state.conversation_context['response'] and state.conversation_context['response']['intent_pr_approver'] == 'true':
                response = self.get_pr_approver(state, watson_response['output']['text'][0])
            elif state.conversation_context['response'] and state.conversation_context['response']['intent_vendor_availability'] == 'true':
                response = self.check_vendor_availability(state,
                                                          watson_response['output']['text'][0])
            else:
                response = self.handle_start_message(state, watson_response)
        except Exception:
            print(sys.exc_info())
            # clear state and set response
            self.clear_user_state(state)
            response = "Sorry, something went wrong! Say anything to me to start over..."
        # post response to slack
        self.post_to_slack(response, channel)

    def handle_start_message(self, state, watson_response):
        response = ''
        for text in watson_response['output']['text']:
            response += text + "\n"
        return response

    def get_po_status(self, state, message):
        # we want to get a status of po number provided by user
        # get the status of the po by making rest api call
        po_status = self.bot_client.get_po_status(state.conversation_context['response']['po_number'])
        # build and return response
        if 'status' in po_status:
            response = message + po_status['status'].lower()
        elif 'exception' in po_status:
            response = po_status['exception']
        else:
            response = "Data is not available for given details."
        # Clear conversation context 
        state.conversation_context = None
        return response

    def get_pr_approver(self, state, message):
        # we want to get approver of pr number provided by user
        # get the approver of the pr number by making rest api call
        pr_approver = self.bot_client.get_pr_approver(state.conversation_context['response']['pr_number'])
        # build and return response
        if 'pr_approver' in state.conversation_context['response'] and 'pr_approver' in pr_approver:
            if state.conversation_context['response']['pr_approver'].lower() == pr_approver['pr_approver'].lower():
                response = 'Yes.' + message + pr_approver['pr_approver']
            else:
                response = 'No.' + message + pr_approver['pr_approver']
        elif 'pr_approver' in pr_approver:
            response = message + pr_approver['pr_approver']
        elif 'exception' in pr_approver:
            response = pr_approver['exception']
        else:
            response = "Data is not available for given details."
        # Clear conversation context 
        state.conversation_context = None
        return response

    def check_vendor_availability(self, state, message):
        # We want to check vendor availability
        # Check the vendor availability by making rest api call
        countries = pycountry.countries
        for i in countries:
            if i.name.lower() == state.conversation_context['response']['location'].lower():
                country = i.alpha_2
        vendor_status = self.bot_client.check_vendor_availability(
            state.conversation_context['response']['system_value'],
            state.conversation_context['response']['supplier_value'],
            country)
        # build and return response
        if 'countries' in vendor_status:
            for i in vendor_status['countries']:
                for j in countries:
                    if i.lower() == j.alpha_2.lower():
                        message = message + j.name + ","
            if country in vendor_status:
                country_validation = "Yes available"
            else:
                country_validation = "No, not available"
            response = country_validation + message[:-1].lower()
        elif 'exception' in vendor_status:
            response = vendor_status['exception']
        else:
            response = "Data is not available for given details."
        # Clear conversation context 
        state.conversation_context = None
        return response

    @staticmethod
    def clear_user_state(state):
        state.ingredient_cuisine = None
        state.conversation_context = None
        state.conversation_started = False

    def run(self):
        while self.running:
            if self.slack_client.rtm_connect():
                print("Chatbot is connected and running!")
                while self.running:
                    slack_output = self.slack_client.rtm_read()
                    message, message_sender, channel = self.parse_slack_output(slack_output)
                    if message and channel and message_sender != self.slack_bot_id:
                        self.handle_message(message, message_sender, channel)
                    time.sleep(self.delay)
            else:
                print("Connection failed. Invalid Slack token or bot ID?")
        print("watson chatbot is shutting down...")

    def stop(self):
        self.running = False
