import argparse
import os
import pandas as pd

from libs.google_service import Google
from libs.util_service import EmailUtil

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="Path to the config files", default=os.environ.get('CONFIG'))
    parser.add_argument("--spam-list", help="Spam list file", default=os.environ.get('SPAM_LIST'))
    args = parser.parse_args()

    google = Google(args.config)
    google.get_google_service()

    email_util = EmailUtil()
    email_util.read_spam_list(args.spam_list)
    print(email_util.spam_list)


