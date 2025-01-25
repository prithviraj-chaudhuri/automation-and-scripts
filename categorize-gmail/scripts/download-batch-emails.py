import os
import argparse
import datetime
import json
import csv

from google_service import Google

class Instance:
    def __init__(self, data, start_date, end_date):
        if not start_date:
            start_date = 'start'
        if not end_date:
            end_date = 'end'
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
    parser.add_argument("--spam", help="Process spam", default=os.environ.get('SPAM'))
    args = parser.parse_args()

    instance = Instance(args.data, args.start_date, args.end_date)
    if not instance.is_instance_started():
        instance.start_instance()
    else:
        print("Process already running for dates between ", args.start_date, " ", args.end_date)
        exit

    google = Google(args.config, instance)
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
        after_date = ''

    if args.end_date:
        before_date = int(datetime.datetime.strptime(args.end_date, '%Y-%m-%d').timestamp())
    else:
        before_date = ''

    spam = False
    if args.spam:
        print("Processing spam emails")
        spam = True

    messages, first_page_token, next_page_token = google.list_messages('me', after_date, before_date, int(args.pages_to_process), first_page_token, spam)
    emails = google.get_messages(messages)

    if len(emails) > 1:
        instance.update_instance(next_page_token, file_count+1, True)
        write_csv(emails, args.data, file_count)
    else:
        print("NO_EMAILS")
        
    print(f"Next Page Token {next_page_token}")