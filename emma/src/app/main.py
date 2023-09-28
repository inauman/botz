import os, time
from flask import Flask, request, jsonify
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import find_dotenv, load_dotenv

# Load environment variables from .env file
load_dotenv(find_dotenv())

# Set Slack API credentials
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]
SLACK_BOT_USER_ID = os.environ["SLACK_BOT_USER_ID"]

app = Flask(__name__)

# Initialize the Slack client with your token
slack_client = WebClient(token=SLACK_BOT_TOKEN)

def get_bot_user_id():
    try:
        response = slack_client.auth_test()
        bot_user_id = response["user_id"]
        print(f"Bot user ID: {bot_user_id}")
        return bot_user_id
    except SlackApiError as e:
        print(f"Error: {e}")

@app.route('/api/slack/events', methods=['POST'])
def slack_events():
    data = request.json
    #print(f"Received Slack event: {data}")
    
    if data.get("type") == 'url_verification':
        return jsonify({"challenge": data.get("challenge")})

    elif 'event' in data:
        event_data = data['event']
        if event_data.get('type') in ['app_mention', 'message']:
            return handle_app_mention_direct_chat(event_data)
    
    return jsonify({"status": "ok"})

def handle_app_mention_direct_chat(event_data):
    # Don't process the event if it's a bot message
    if event_data.get('subtype') == 'bot_message':
        return jsonify({"status": "skipped bot message"})

    # Don't process the event if the message was sent by the bot itself
    if event_data.get('user') == SLACK_BOT_USER_ID:
        return jsonify({"status": "skipped own message"})

    user_message = event_data.get('text', '')
    response = generate_response(user_message)
    send_message_to_slack(response, event_data['channel'])
    
    return jsonify({"status": "handled event"})

def generate_response(message):
    if "hello" in message.lower():
        return "Hello! How can I assist you?"
    else:
        return "I'm not sure how to respond to that."

def send_message_to_slack(message, channel):
    try:
        response = slack_client.chat_postMessage(channel=channel, text=message)
    except SlackApiError as e:
        print(f"Error sending message to Slack: {e.response['error']}")

def run():
    print("calling run")
    # Code to run your Flask app
    app.run(port=5000)

if __name__ == '__main__':
    run()
