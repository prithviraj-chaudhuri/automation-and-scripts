import argparse
import os
import pandas as pd

from libs.google_service import Google
from libs.util_service import EmailUtil

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="Path to the config files", default=os.environ.get('CONFIG'))
    parser.add_argument("--data", help="Path to the store the exported files", default=os.environ.get('DATA'))
    args = parser.parse_args()

    email_util = EmailUtil()
    email_util.read_email_data(args.data)
    email_util.generate_sender_report(args.data)




    


    
