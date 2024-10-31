wget https://raw.githubusercontent.com/prithviraj-chaudhuri/automation-and-scripts/refs/heads/main/categorize-gmail/download-batch-emails.py -O download-batch-emails.py
wget https://raw.githubusercontent.com/prithviraj-chaudhuri/automation-and-scripts/refs/heads/main/requirements.txt -O requirements.txt
pip install -r requirements.txt
mkdir -p /saved_data/gmail-categorize
python3 download-batch-emails.py --config=/secrets --data=/saved_data/gmail-categorize --pages_to_process=5 --update_status_count=20