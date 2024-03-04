from notion_client import Client
import sys
import dotenv
import os

def create_quick_note(note):
    notion_client = Client(auth=os.getenv("NOTION_TOKEN"))
    new_note = {
        "Name":  {
            "id": "title",
            "type": "title",
            "title": [
                {
                    "type": "text",
                    "text": {
                        "content": note,
                        "link": None
                    },
                    "plain_text": note,
                    "href": None
                }
            ]
        }
    }
    notion_client.pages.create(parent={"database_id": os.getenv("QUICK_NOTE")}, properties=new_note)


if __name__ == '__main__':
    dotenv.load_dotenv("config/.env")
    if len(sys.argv) > 1:
        create_quick_note(sys.argv[1])
    else:
        print("No Quick note created")