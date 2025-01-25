Earliest 2014-03-01

`python download-batch-emails.py --config=../config --data=data/inbox --pages_to_process=30 --update_status_count=10 --start_date=2024-11-10 --end_date=2024-11-11`
`python analyze-emails.py --data=./data/inbox --config=../../config`
`python download-batch-emails.py --config=../../config --data=data/spam --pages_to_process=30 --spam=True`
`python analyze-emails.py --data=./data/spam --config=../../config`


`python send-emails-to-spam.py --config=../../config --data=./data/inbox --spam-list=./data/spam_list.csv > ./data/output/run1.log`