from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import os
import base64
import argparse
import datetime
import json
import csv

class Instance:
    def __init__(self, data, start_date, end_date):
        self.status_file = data + '/status--'+start_date+'--'+end_date+'.json'
        self.status = None

    def is_instance_started(self):
        try:
            with open(self.status_file) as f:
                self.status = json.load(f)
                return not self.status["is_complete"]
        except:
            return False

    def start_instance(self):
        if not self.status:
            self.status = {
                "next_page": '',
                "file": 1,
                "is_complete": False
            }
        else:
            self.status["is_complete"] = False
        with open(self.status_file,'w') as outfile:
            json.dump(self.status, outfile)

    def update_instance(self, next_page_token, file_count, is_complete):
        self.status = {
            "next_page": next_page_token,
            "file": file_count,
            "is_complete": is_complete
        }
        with open(self.status_file, 'w') as outfile:
            json.dump(self.status, outfile)

class Google:
    def __init__(self, config_path, instance):
        self.config_path = config_path
        self.SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
        self.service = None
        self.instance = instance

    def get_google_service(self):
        creds = None
        token_gmail = self.config_path + "/token-gmail.json"
        if os.path.exists(token_gmail):
            creds = Credentials.from_authorized_user_file(token_gmail, self.SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.config_path + "/credentials.json", self.SCOPES
                )
                creds = flow.run_local_server(port=0)
                with open(token_gmail, "w") as token:
                    token.write(creds.to_json())
        try:
            service = build("gmail", "v1", credentials=creds)
            self.service = service
        except:
            print("No service")

    def list_messages(self, user_id='me', after_date=None, before_date=None, pages_to_process=-1, next_page_token=None):
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
            response = None
            if next_page_token:
                print(next_page_token)
                response = self.service.users().messages().list(userId=user_id, q=query.strip(), pageToken=next_page_token).execute()
            else:
                response = self.service.users().messages().list(userId=user_id, q=query.strip()).execute()
            messages = response.get('messages', [])
            first_page_token = next_page_token

            page_count = 1
            next_page_token = None
            while 'nextPageToken' in response:
                next_page_token = response['nextPageToken']
                print(next_page_token)
                if pages_to_process == page_count:
                    break
                response = self.service.users().messages().list(userId=user_id, q=query.strip(), pageToken=next_page_token).execute()
                messages.extend(response.get('messages', []))
                page_count += 1
            
            print(f"Retrieved message count: {len(messages)}")
            return messages, first_page_token, next_page_token
        
        except HttpError as error:
            print(f"An error occurred: {error}")
            return [], None
        
    def get_messages(self, messages):
        emails = []

        print("Processing Messages")
        for message in messages:
            current_message_id = message['id']
            print(current_message_id)
            email_data = self.get_message('me', message['id'])
            emails.append(email_data)

        return emails
    
    def get_message(self, user_id, msg_id):
        try:
            message = self.service.users().messages().get(userId=user_id, id=msg_id).execute()
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
    

def write_csv(emails, data, file_count):
    print("Writting to file")
    keys = sorted(emails[0].keys())
    with open(data + '/emails-' + str(file_count) + '.csv', 'w', newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(emails)

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="Path to the config files", default=os.environ.get('CONFIG'))
    parser.add_argument("--data", help="Path to the store the exported files", default=os.environ.get('DATA'))
    parser.add_argument("--pages_to_process", help="Number of pages to process", default=os.environ.get('PAGES_TO_PROCESS'))
    parser.add_argument("--start_date", help="The date from which to pull messages (yyyy-mm-dd)", default=os.environ.get('START_DATE'))
    parser.add_argument("--end_date", help="The date till which to pull messages (yyyy-mm-dd)", default=os.environ.get('END_DATE'))
    parser.add_argument("--page_token", help="Page token to start processing from", default=os.environ.get('PAGE_TOKEN'))
    args = parser.parse_args()

    instance = Instance(args.data, args.start_date, args.end_date)
    if not instance.is_instance_started():
        instance.start_instance()
    else:
        print("Process already running for dates between ", args.start_date, " ", args.end_date)
        exit

    google  = Google(args.config, instance)
    google.get_google_service()
    
    first_page_token = None

    file_count = 1
    if instance.status:
        first_page_token = instance.status['next_page']
        file_count = int(instance.status['file'])
    else:
        first_page_token = args.page_token

    if args.start_date:
        after_date = int(datetime.datetime.strptime(args.start_date, '%Y-%m-%d').timestamp())
    else:
        after_date = None

    if args.end_date:
        before_date = int(datetime.datetime.strptime(args.end_date, '%Y-%m-%d').timestamp())
    else:
        before_date = None

    messages, first_page_token, next_page_token = google.list_messages('me', after_date, before_date, int(args.pages_to_process), first_page_token)
    emails = google.get_messages(messages)

    if len(emails) > 1:
        instance.update_instance(next_page_token, file_count+1, True)
        write_csv(emails, args.data, file_count)
        
    print(f"Next Page Token {next_page_token}")