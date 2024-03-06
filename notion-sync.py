from notion_client import Client
from oauth2client import client

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import dotenv
import os
import os.path

def get_google_service():
    SCOPES = ["https://www.googleapis.com/auth/calendar"]
    creds = None
    if os.path.exists("config/token.json"):
        creds = Credentials.from_authorized_user_file("config/token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "config/credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
            with open("config/token.json", "w") as token:
                token.write(creds.to_json())
    try:
        service = build("calendar", "v3", credentials=creds)
        return service
    except:
        print("No service")
        return None

def get_kanban_tasks():
    notion_client = Client(auth=os.getenv("NOTION_TOKEN"))
    kanban_board = notion_client.databases.query(
        **{
            "database_id": os.getenv("KANBAN_ID"),
            "filter": {
                "and" : [
                    {
                        "property": "Send to Google Calendar",
                        "checkbox": {
                            "equals": True
                        },
                    },
                    {
                        "property": "Due Date",
                        "date": {
                            "is_not_empty": True
                        },
                    },
                ]
                
            },
        }
    )
    tasks = kanban_board["results"]
    return tasks, notion_client

def create_or_update_google_events(service, notion_client, tasks):
    for task in tasks:
        task_id = task["id"]
        event_name = task["properties"]["Name"]["title"][0]["text"]["content"]
        event_start_date = task["properties"]["Due Date"]["date"]["start"]
        event_end_date = task["properties"]["Due Date"]["date"]["end"]
        event_gcal_link = task["properties"]["Google Calendar Id"]["rich_text"]

        if event_end_date is None:
            event_end_date = event_start_date
            
        event_body = {
                'summary': event_name,
                'start': {
                    'dateTime': event_start_date,
                    'timeZone': 'America/Los_Angeles',
                },
                'end': {
                    'dateTime': event_end_date,
                    'timeZone': 'America/Los_Angeles',
                },
                'recurrence': [
                ],
                'attendees': [
                ],
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 24 * 60},
                        {'method': 'popup', 'minutes': 30},
                    ],
                },
            }

        if len(event_gcal_link) == 0:
            print("Creating event")
            event = service.events().insert(calendarId='primary', body=event_body).execute()
            notion_client.pages.update(
                task_id,
                properties={
                    "Google Calendar Id": {
                        "rich_text": [{"type": "text", "text": {"content": event.get('id')}}]
                    }
                },
            )
        else:
            print("Updating event")
            event_id = event_gcal_link[0]["text"]["content"]
            event = service.events().update(calendarId='primary', eventId=event_id, body=event_body).execute()

if __name__ == '__main__':
    dotenv.load_dotenv("config/.env")
    tasks, notion_client = get_kanban_tasks()
    service = get_google_service()
    create_or_update_google_events(service, notion_client, tasks)
