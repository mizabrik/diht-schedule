import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
CALENDAR = 'aldblom3gns6jj3dm8e9fhvcso@group.calendar.google.com'
NLP_CALENDAR = '5080jr4fj2hkko4vop9fvu54tk@group.calendar.google.com'
FIELDS = ['colorId', 'description', 'end', 'location', 'recurrence', 'start', 'summary']

def crop_event(event):
    return {k: v for k, v in event.items() if k in FIELDS}

def get_nlp_events(service):
    def transform_event(event):
        if event['summary'].endswith('workshop'):
            event['colorId'] = '7'
            event['description'] = 'Семинар, Алексей Андреевич Сорокин\n' + event['summary']
        else:
            event['colorId'] = '3'
            event['description'] = 'Лекция, Алексей Андреевич Сорокин'
        event['summary'] = 'Глубокое обучение в обработке естественного языка'
        event['location'] = 'Оксфорд ШАД'
        return crop_event(event)

    events = service.events().list(calendarId=NLP_CALENDAR).execute()['items']
    return [transform_event(e) for e in events if e['status'] != 'cancelled' and not e['summary'].startswith('DEADLINE')]


def main():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)

    events_result = service.events().list(calendarId=CALENDAR).execute()
    events = events_result.get('items', [])
    for event in events:
        print(crop_event(event))
    for event in get_nlp_events(service):
        print(event)


if __name__ == '__main__':
    main()
