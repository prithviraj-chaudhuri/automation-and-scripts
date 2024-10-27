from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import dotenv
import os
import base64
import argparse
import datetime
import json
import csv


def get_google_service(config_path):
    SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
    creds = None
    token_gmail = config_path + "/token-gmail.json"
    if os.path.exists(token_gmail):
        creds = Credentials.from_authorized_user_file(token_gmail, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                config_path + "/credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
            with open(token_gmail, "w") as token:
                token.write(creds.to_json())
    try:
        service = build("gmail", "v1", credentials=creds)
        return service
    except:
        print("No service")
        return None

def list_messages(service, user_id='me', after_date=None, before_date=None, pages_to_process=-1, next_page_token=None):
    print("Processing pages")
    query = ''
    if after_date:
        query += f'after:{after_date} '
    if before_date:
        query += f'before:{before_date}'
    
    if query == '':
        query = 'is:read'

    first_page_token = None
    messages = []
    try:
        if next_page_token:
            print(next_page_token)
            response = service.users().messages().list(userId=user_id, q=query.strip(), pageToken=next_page_token).execute()
            messages = response.get('messages', [])
        else:
            response = service.users().messages().list(userId=user_id, q=query.strip()).execute()
            messages = response.get('messages', [])
        first_page_token = next_page_token

        page_count = 1
        next_page_token = None
        while 'nextPageToken' in response:
            next_page_token = response['nextPageToken']
            print(next_page_token)
            if pages_to_process == page_count:
                break
            response = service.users().messages().list(userId=user_id, q=query.strip(), pageToken=next_page_token).execute()
            messages.extend(response.get('messages', []))
            page_count += 1
        
        print(f"Retrieved message count: {len(messages)}")
        return messages, first_page_token, next_page_token
    
    except HttpError as error:
        print(f"An error occurred: {error}")
        return [], None

def update_status(data, next_page_token, next_message_id, file_count):
    print("Saving status")
    stats = {
        "next_page": next_page_token,
        "next_message": next_message_id,
        "file": file_count
    }
    with open(data+"/status.json", "w") as outfile:
        json.dump(stats, outfile)

def write_csv(emails, data, file_count):
    print("Writting to file")
    keys = sorted(emails[0].keys())
    with open(data + '/emails-' + str(file_count) + '.csv', 'w', newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(emails)

def get_messages(service, data_path, first_page_token=None, current_message_id=None, update_status_count=100, file_count=1):
    begin = False
    emails = []
    count = 0

    print("Processing Messages")
    for message in messages:
        if current_message_id and message['id'] == current_message_id:
            begin = True
        elif not current_message_id:
            begin = True
        if not begin:
            continue
        current_message_id = message['id']
        print(current_message_id)
        email_data = get_message(service, 'me', message['id'])
        emails.append(email_data)
        count += 1
        if count == update_status_count:
            update_status(data_path, first_page_token, current_message_id, file_count)
            count = 0

    return emails, current_message_id

def get_message(service, user_id, msg_id):
    try:
        message = service.users().messages().get(userId=user_id, id=msg_id).execute()
        payload = message.get('payload', {}).get('body', {}).get('data')
        if payload:
            email_content = base64.urlsafe_b64decode(payload.encode('UTF-8')).decode('UTF-8')
        else:
            email_content = "No content found."
        
        msg = {
            'id': message['id'],
            # 'snippet': message['snippet'],s
            # 'email_content': email_content
        }

        header = message.get('payload', {}).get('headers', {})
        for info in header:
            if info["name"] == "From":
                msg["sender"] = info["value"]
            if info["name"] == "Date":
                msg["date"] = info["value"]
            if info["name"] == "Subject":
                msg["subject"] = info["value"]
            if info["name"] == "To":
                msg["receiver"] = info["value"]

        return msg
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None

if __name__ == '__main__':
    dotenv.load_dotenv("../config/.env")

    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="Path to the config files")
    parser.add_argument("--data", help="Path to the store the exported files")
    parser.add_argument("--pages_to_process", help="Number of pages to process")
    parser.add_argument("--page_token", help="Page token to start processing from")
    parser.add_argument("--update_status_count", help="Save the current status after processing these many messages")
    parser.add_argument("--message_id", help="Page token to start processing from")
    parser.add_argument("--start_date", help="The date from which to pull messages")
    parser.add_argument("--end_date", help="The date till which to pull messages")
    args = parser.parse_args()

    service = get_google_service(args.config)

    status = None
    try:
        with open(args.data + '/status.json') as f:
            status = json.load(f)
    except:
        print("Status not available")
        status = None

    first_page_token = None
    next_message_id = None
    file_count = 1
    if status:
        first_page_token = status['next_page']
        next_message_id = status['next_message']
        file_count = int(status['file'])
    else:
        first_page_token = args.page_token
        next_message_id = args.message_id

    if args.start_date:
        after_date = int(datetime.datetime.strptime(args.start_date, '%Y-%m-%d').timestamp())
    else:
        after_date = None

    if args.end_date:
        before_date = int(datetime.datetime.strptime(args.end_date, '%Y-%m-%d').timestamp())
    else:
        before_date = None

    messages, first_page_token, next_page_token = list_messages(service, 'me', after_date, before_date, int(args.pages_to_process), first_page_token)
    emails, next_message_id = get_messages(service, args.data, first_page_token, next_message_id, int(args.update_status_count), file_count)

    update_status(args.data, next_page_token, None, file_count+1)
    write_csv(emails, args.data, file_count)
        
    print(f"Next Page Token {next_page_token}")
    print(f"Next message ID {next_message_id}")