import os
import time
import random
from slackclient import SlackClient

# errors to watch for
from slackclient._client import SlackNotConnected # not actually used, see https://github.com/slackapi/python-slackclient/issues/36
from slackclient._server import SlackConnectionError
from websocket import WebSocketConnectionClosedException
from socket import error as SocketError


# starterbot's ID as an environment variable
BOT_ID = os.environ.get("BOT_ID")

# constants
AT_BOT = "<@" + BOT_ID + ">"
RAND_COMMAND = "pick"

# instantiate Slack client
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))


def handle_command(command, channel):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """
    response = "I don't understand anything besides " + RAND_COMMAND + "."
    if command == RAND_COMMAND:
    	response = pick_active_user(channel)
    slack_client.api_call("chat.postMessage", channel=channel,
                          text=response, as_user=True)


def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
    	print output_list
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                # return text after the @ mention, whitespace removed
                return output['text'].split(AT_BOT)[1].strip().lower(), \
                       output['channel']
            elif output and 'type' in output and output['type'] == 'goodbye':
                slack_client.rtm_connect()
    return None, None

def pick_active_user(channel):
	rand_user_id=get_random_user_in_channel(channel)
	if rand_user_id == False:
		return "Well this is embarassing, but that didn't work. Am I in a private room? I respect peoples' privacy too much for that. "
	else:
		user_info=slack_client.api_call("users.info",user=rand_user_id).get('user')
		return user_info.get('real_name') + " <@" + rand_user_id + ">"

def get_random_user_in_channel(channel_id):
	info=slack_client.api_call("channels.info",channel=channel_id)
	print info.get("ok")
	if info.get("ok") == False:
		print "no channel!"
		return False
	else:
		members=info.get('channel').get('members')
		print members
		return random.choice(members)

if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("SortingHat connected and running!")
        while True:
            try:
                command, channel = parse_slack_output(slack_client.rtm_read())
            except (SocketError, WebSocketConnectionClosedException, SlackConnectionError, SlackNotConnected):
                slack_client.rtm_connect()
            else:
                if command and channel:
                    handle_command(command, channel)
                time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")