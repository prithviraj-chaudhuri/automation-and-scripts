from notion_client import Client
from oauth2client import client

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import dotenv
import os
import os.path

dotenv.load_dotenv("config/.env")

# Connect to google
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
except:
    print("No service")

# Connect to Notion and query the kanban board
client = Client(auth=os.getenv("NOTION_TOKEN"))
kanban_board = client.databases.query(
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
                    "property": "Google Calendar Link",
                    "rich_text": {
                        "is_empty": True
                    },
                },
            ]
            
        },
    }
)

tasks = kanban_board["results"]
google_cal_events = []

# Loop through page tasks and create events in google calendar
for task in tasks:
    task_id = task["id"]
    event_name = task["properties"]["Name"]["title"][0]["text"]["content"]
    event_start_date = task["properties"]["Due Date"]["date"]["start"]
    event_end_date = task["properties"]["Due Date"]["date"]["end"]
    if event_end_date is None:
        event_end_date = event_start_date
        
    event = {
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
    event = service.events().insert(calendarId='primary', body=event).execute()
    client.pages.update(
        task_id,
        properties={
            "Google Calendar Link": {
                "rich_text": [{"type": "text", "text": {"content": event.get('htmlLink')}}]
            }
        },
    )

