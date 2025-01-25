import os
import pandas as pd

class EmailUtil:

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
    
    def read_spam_list(self, spam_list_file):
        self.spam_list = pd.read_csv(spam_list_file)

    def get_potential_spam_emails(self):
        matched_senders = self.sender_counts[self.sender_counts['sender_email'].isin(self.spam_list['sender_email'])]
        return matched_senders
    
    def generate_sender_report(self, data_directory):
        self.sender_counts = self.sender_counts.sort_values(by='count', ascending=False)
        self.sender_counts.to_csv(data_directory+'/sender_counts.csv', index=False)