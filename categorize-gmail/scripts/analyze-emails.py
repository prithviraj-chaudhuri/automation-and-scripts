import argparse
import os
import pandas as pd

from google_service import Google

class EmailData:

    def __init__(self):
        self.emails = {}
        self.spam_list = None
        self.sender_counts = None

    def read_email_data(self, data_directory):
        for root, dirs, files in os.walk(data_directory):
            for filename in files:
                print("Reading file: ", filename)
                if filename.startswith('emails') and filename.endswith('.csv'):
                    file_path = os.path.join(root, filename)
                    df_name = os.path.relpath(file_path, data_directory).replace('/', '_').replace('\\', '_')
                    self.emails[df_name] = pd.read_csv(file_path)
        all_emails = pd.concat(self.emails.values())
        all_emails[['sender_name', 'sender_email']] = all_emails['sender'].str.extract(r'(?:"?([^"]*)"?\s)?(?:<?(.+@[^>]+)>?)')
        self.sender_counts = all_emails.groupby('sender_email').size().reset_index(name='count')
    
    def read_spam_list(self, data_directory):
        self.spam_list = pd.read_csv(data_directory+'/spam.csv')

    def get_potential_spam_emails(self):
        matched_senders = self.sender_counts[self.sender_counts['sender_email'].isin(self.spam_list['sender_email'])]
        return matched_senders
    
    def generate_sender_report(self, data_directory):
        self.sender_counts = self.sender_counts.sort_values(by='count', ascending=False)
        self.sender_counts.to_csv(data_directory+'/sender_counts.csv', index=False)

    def get_current_spam_emails(self):
        google = Google(args.config)
        google.get_google_service()
        spam_emails = google.get_spam_emails()
        spam_emails_df = pd.DataFrame(spam_emails, columns=['sender', 'subject', 'snippet'])
        print(spam_emails_df)
        spam_emails_df[['sender_name', 'sender_email']] = spam_emails_df['sender'].str.extract(r'(?:"?([^"]*)"?\s)?(?:<?(.+@[^>]+)>?)')
        grouped_spam_emails = spam_emails_df.groupby('sender_email').size().reset_index(name='count')
        return grouped_spam_emails

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="Path to the config files", default=os.environ.get('CONFIG'))
    parser.add_argument("--data", help="Path to the store the exported files", default=os.environ.get('DATA'))
    args = parser.parse_args()

    email_data = EmailData()
    email_data.read_email_data(args.data)
    # email_data.generate_sender_report(args.data)

    email_data.read_spam_list(args.data)
    print("Potential Spam emails:")
    print(email_data.get_potential_spam_emails())

    # Send emails to spam here
    print(email_data.get_current_spam_emails())




    


    
