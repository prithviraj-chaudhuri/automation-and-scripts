FROM python:3.9.20

COPY requirements.txt requirements.txt
COPY download-batch-emails.py download-batch-emails.py

RUN pip install -r requirements.txt

ENV CONFIG=/config
ENV DATA=/data
ENV PAGES_TO_PROCESS=100
ENV UPDATE_STATUS_COUNT=20
ENV START_DATE=2024-11-10
ENV END_DATE=2024-11-11

ENTRYPOINT python download-batch-emails.py