from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import dotenv
import os
import base64


def get_google_service():
    SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
    creds = None
    if os.path.exists("../config/token-gmail.json"):
        creds = Credentials.from_authorized_user_file("../config/token-gmail.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "../config/credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
            with open("../config/token-gmail.json", "w") as token:
                token.write(creds.to_json())
    try:
        service = build("gmail", "v1", credentials=creds)
        return service
    except:
        print("No service")
        return None

def get_emails(service):
    emails = service.users().messages().list(userId='me', labelIds=['INBOX'], q="is:read", maxResults=600).execute()
    messages = emails.get('messages', [])
    final_messages = []
    for message in messages:
        msg_obj = {}
        msg = service.users().messages().get(userId='me', id=message['id']).execute()

        msg_obj = {}
        msg_snippet = msg['snippet']
        msg_headers = msg['payload']['headers']

        sender = next(header['value'] for header in msg_headers if header['name'] == 'From')

        if 'parts' in msg['payload']:
            for part in msg['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    body = part['body']['data']
        else:
            body = msg['payload']['body']['data']
        
        # print(sender)
        if '<' in sender:
            msg_obj['from'] = sender.split('<')[1]
        else:
            msg_obj['from'] = sender

        # msg_obj['snippet'] = msg_snippet
        # msg_obj['body'] = base64.urlsafe_b64decode(body).decode('utf-8')
        final_messages.append(msg_obj)
    return final_messages

if __name__ == '__main__':
    dotenv.load_dotenv("../config/.env")
    service = get_google_service()
    emails = get_emails(service)
    print(len(emails))

