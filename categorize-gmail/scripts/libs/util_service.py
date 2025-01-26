import os
import pandas as pd

class EmailUtil:

    def __init__(self):
        self.emails = None
        self.spam_list = None
        self.sender_counts = None
        self.spam_emails = None

    def __read_email_data(self, data_directory):
        emails = {}
        for root, dirs, files in os.walk(data_directory):
            for filename in files:
                print("Reading file: ", filename)
                if filename.startswith('emails') and filename.endswith('.csv'):
                    file_path = os.path.join(root, filename)
                    df_name = os.path.relpath(file_path, data_directory).replace('/', '_').replace('\\', '_')
                    emails[df_name] = pd.read_csv(file_path)
        emails_pd = pd.concat(emails.values())
        emails_pd[['sender_name', 'sender_email']] = emails_pd['sender'].str.extract(r'(?:"?([^"]*)"?\s)?(?:<?(.+@[^>]+)>?)')
        return emails_pd

    def read_email_data(self, data_directory):
        self.emails = self.__read_email_data(data_directory)
        print("Emails: ")
        print(self.emails.head())
        self.sender_counts = self.emails.groupby('sender_email').size().reset_index(name='count')

    def read_spam_email_data(self, data_directory):
        self.spam_emails = self.__read_email_data(data_directory)
        print("Spam Emails: ")
        print(self.spam_emails.head())
    
    def read_spam_list(self, spam_list_file):
        self.spam_list = pd.read_csv(spam_list_file)
        print("Spam List: ")
        print(self.spam_list.head())

    def get_message_ids_from_spam_list(self):
        spam_emails = self.emails[
            self.emails['sender_email'].isin(self.spam_list['sender_email'])
        ]
        print("Spam emails: ")
        print(spam_emails.head())
        return spam_emails['id'].values.tolist()
    
    def generate_sender_report(self, data_directory):
        self.sender_counts = self.sender_counts.sort_values(by='count', ascending=False)
        self.sender_counts.to_csv(data_directory+'/sender_counts.csv', index=False)