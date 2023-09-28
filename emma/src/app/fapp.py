import os, time
import logging
from typing import Dict
from fastapi import FastAPI, Request, BackgroundTasks, Body
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import find_dotenv, load_dotenv
from pydantic import BaseModel


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

# Load environment variables from .env file
load_dotenv(find_dotenv())

# Set Slack API credentials
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]
SLACK_BOT_USER_ID = os.environ["SLACK_BOT_USER_ID"]

app = FastAPI()

# Initialize the Slack client with your token
slack_client = WebClient(token=SLACK_BOT_TOKEN)

def get_bot_user_id():
    try:
        response = slack_client.auth_test()
        bot_user_id = response["user_id"]
        log.info(f"Bot user ID: {bot_user_id}")
        return bot_user_id
    except SlackApiError as e:
        log.info(f"Error: {e}")

class SlackEvent(BaseModel):
    type: str
    event: dict


@app.post('/api/slack/events')
async def slack_events(request: Request, background_tasks: BackgroundTasks, body: Dict = Body(...)):
    log.debug(f"Received Slack event: {body}")
    
    retry_num = request.headers.get('X-Slack-Retry-Num')
    if retry_num:
        print(f"Slack retry number: {retry_num}")
    
    if body["type"] == 'url_verification':
        return {"challenge": body.get("challenge", "")}

    elif 'event' in body and (body["event"].get('type') == 'app_mention' or (body["event"].get('type') == 'message' and body["event"].get('channel_type') == 'im')):
        # This will start the event handling in the background
        background_tasks.add_task(handle_app_mention_direct_chat, body["event"])
    
    return {"status": "ok"}


def handle_app_mention_direct_chat(event_data: dict):
    # Don't process the event if it's a bot message
    if event_data.get('subtype') == 'bot_message':
        return {"status": "skipped bot message"}
    
    # Don't process the event if the message was sent by the bot itself
    if event_data.get('user') == SLACK_BOT_USER_ID:
        return {"status": "skipped own message"}
    
    user_message = event_data.get('text', '')
    response = generate_response(user_message)
    send_message_to_slack(response, event_data['channel'])
    return {"status": "handled app_mention"}


def generate_response(message: str):
    if "hello" in message.lower():
        #time.sleep(10)
        return "Hello! How can I assist you?"
    else:
        return "I'm not sure how to respond to that."

def send_message_to_slack(message: str, channel: str):
    try:
        response = slack_client.chat_postMessage(channel=channel, text=message)
    except SlackApiError as e:
        print(f"Error sending message to Slack: {e.response['error']}")
