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
    return tasks
    

if __name__ == '__main__':
    dotenv.load_dotenv("config/.env")
    tasks = get_archived_notion_tasks()
    archive_location = os.getenv("ARCHIVE_LOCATION")
    date_time = datetime.today().strftime('%Y-%m-%d-%H-%M-%S')
    filename = archive_location + '/' + date_time + '.json'
    with open(filename, 'w') as f:
        json.dump(tasks, f)
    
