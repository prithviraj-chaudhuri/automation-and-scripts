import argparse
import os
import pandas as pd

from libs.google_service import Google
from libs.util_service import EmailUtil

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="Path to the config files", default=os.environ.get('CONFIG'))
    parser.add_argument("--data", help="Path to the data files", default=os.environ.get('DATA'))
    parser.add_argument("--spam-list", help="Spam list file", default=os.environ.get('SPAM_LIST'))
    args = parser.parse_args()

    email_util = EmailUtil()
    email_util.read_email_data(args.data)
    email_util.read_spam_list(args.spam_list)

    message_ids = email_util.message_ids_in_emails_not_in_spam_list()
    print("Not Spam email count: ", str(len(message_ids)))

    google = Google(args.config)
    google.get_google_service()
    google.train_spam_filter(message_ids, spam=False)