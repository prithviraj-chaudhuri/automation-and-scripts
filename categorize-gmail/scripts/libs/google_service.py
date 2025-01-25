from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import base64
import os

class Google:
    def __init__(self, config_path, instance=None):
        self.config_path = config_path
        self.SCOPES = [
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.modify"
        ]
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

    def list_messages(self, user_id='me', after_date=None, before_date=None, pages_to_process=-1, next_page_token=None, spam=False):
        print("Processing pages")
        query = ''
        if after_date and after_date != '':
            query += f'after:{after_date}'
        if before_date and before_date != '':
            query += f' before:{before_date}'
        if spam:
            query += ' is:spam'
        
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

    def train_spam_filter(self, message_ids, batch_size=1000):
        results = {
            'marked_spam': 0,
            'trained_filter': 0,
            'failed': 0
        }
        
        for i in range(0, len(message_ids), batch_size):
            batch = message_ids[i:i + batch_size]
            print(f"Processing batch {i} to {i + batch_size}")
            print(batch)
            try:
                # Mark as spam and train filter
                batch_request = {
                    'ids': batch,
                    'addLabelIds': ['SPAM'],
                    'removeLabelIds': ['INBOX'],
                    'processForFilter': True
                }
                
                self.service.users().messages().batchModify(
                    userId='me',
                    body=batch_request
                ).execute()
                
                results['marked_spam'] += len(batch)
                results['trained_filter'] += len(batch)
                
            except HttpError as error:
                print(f"Batch error at index {i}: {error}")
                results['failed'] += len(batch)
                
        return results