from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import dotenv
import os
import base64

import langroid.language_models as lm
import langroid as lr

def get_google_service():
    SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
    creds = None
    if os.path.exists("config/token-gmail.json"):
        creds = Credentials.from_authorized_user_file("config/token-gmail.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "config/credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
            with open("config/token-gmail.json", "w") as token:
                token.write(creds.to_json())
    try:
        service = build("gmail", "v1", credentials=creds)
        return service
    except:
        print("No service")
        return None

def get_unread_emails(service):
    emails = service.users().messages().list(userId='me', labelIds=['INBOX'], q="is:unread").execute()
    final_messages = []
    for email in emails['messages']:
        msg = service.users().messages().get(userId='me', id=email['id']).execute()
        msg_obj = {}
        email_data = msg['payload']['headers']
        for values in email_data:
            name = values['name']
            if name == 'From':
                from_name = values['value']     
                snippet = msg['snippet']           
                # for part in msg['payload']['parts']:
                #     try:
                #         data = part['body']["data"]
                #         byte_code = base64.urlsafe_b64decode(data)
                #         text = byte_code.decode("utf-8")
                msg_obj = "FROM: " + from_name + "\n\n"
                msg_obj += "BODY: " + snippet
                    # except BaseException as error:
                    #     pass 
        final_messages.append(msg_obj)
    return final_messages

def get_langroid_agent(host, model, context_length):
    llm_config = lm.OpenAIGPTConfig(
        api_base=host,
        chat_model=model,
        chat_context_length=context_length
    )
    agent_config = lr.ChatAgentConfig(
        llm=llm_config,
        system_message="You are an email categorizing agent. You take the the email body as an input and you categorize the email one of spam, important, bills. Provide your output as a single word",
    )
    agent = lr.ChatAgent(agent_config)
    return agent

if __name__ == '__main__':
    dotenv.load_dotenv("../config/.env")
    service = get_google_service()
    emails = get_unread_emails(service)
    print(emails)
    agent = get_langroid_agent("http://HOME/v1", "phi:latest", 2048)
    for email in emails:
        response = agent.llm_response(email)
        print(response)
