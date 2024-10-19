from notion_client import Client
from datetime import datetime

import logging
import dotenv
import os
import os.path
import json

def get_archived_notion_tasks():
    notion_client = Client(
        auth=os.getenv("NOTION_TOKEN"),
        log_level=logging.INFO
    )
    archive_board = notion_client.databases.query(
        **{
            "database_id": os.getenv("ARCHIVE")
        }
    )
    tasks = archive_board["results"]
    print("Retrieved " + str(len(tasks)) + " archived tasks")
    return tasks, notion_client
    
def archive_tasks(tasks, notion_client):
    for task in tasks:
        notion_client.pages.update(
            **{
                "page_id": task['id'],
                "archived": True
            }
        )

if __name__ == '__main__':
    dotenv.load_dotenv("config/.env")
    tasks, notion_client = get_archived_notion_tasks()
    if len(tasks) > 0:
        archive_location = os.getenv("ARCHIVE_LOCATION")
        date_time = datetime.today().strftime('%Y-%m-%d-%H-%M-%S')
        filename = archive_location + '/' + date_time + '.json'
        with open(filename, 'w') as f:
            json.dump(tasks, f)
        print("Trashing tasks")
        archive_tasks(tasks, notion_client)
    else:
        print("No tasks to archive")