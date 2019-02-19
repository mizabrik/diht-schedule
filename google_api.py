from functools import wraps

import flask
import flask.json.tag
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
import requests

CLIENT_SECRETS_FILE = "client_secrets.json"
SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/calendar',
]

class GoogleAPI:
    def __init__(self, credentials):
        self._calendar_service = googleapiclient.discovery.build(
            'calendar', 'v3', credentials=flask.session['credentials'])
        self._oauth_service = googleapiclient.discovery.build(
            'oauth2', 'v1', credentials=flask.session['credentials'])

    def get_user_email(self):
        request = self._oauth_service.userinfo().get(fields='email')
        return request.execute()['email']

    def get_writable_calendars(self):
        calendars = []
        def add_calendars(response):
            for calendar in response.get('items', []):
                if calendar['accessRole'] in ['writer', 'owner']:
                    calendars.append((calendar['id'], calendar['summary']))

        request = self._calendar_service.calendarList().list()
        response = request.execute()
        add_calendars(response)
        while 'nextPageToken' in response:
            request = self._calendar_service.calendarList().list_next(
                    request, response)
            response = request.execute()
            add_calendars(response)

        return calendars

    def create_calendar(self, name):
        return self._calendar_service.calendars().insert(body={
            'timeZone': 'Europe/Moscow',
            'summary': name,
        }).execute()['id']

    def create_events(self, calendar, events):
        request = self._calendar_service.new_batch_http_request()
        for event in events:
            request.add(self._calendar_service.events().insert(
                  calendarId=calendar, body=event))
        request.execute()

    @staticmethod
    def get_authentication_url(callback_uri):
        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
              CLIENT_SECRETS_FILE, scopes=SCOPES, redirect_uri=callback_uri)
        return flow.authorization_url(access_type='offline')

    @staticmethod
    def process_authentication_response(response, state, callback_uri):
        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
              CLIENT_SECRETS_FILE, scopes=SCOPES, redirect_uri=callback_uri)
        flow.fetch_token(authorization_response=response)
        return flow.credentials

    @staticmethod
    def revoke_token(credentials):
        return requests.post('https://accounts.google.com/o/oauth2/revoke',
            params={'token': credentials},
            headers = {'content-type': 'application/x-www-form-urlencoded'})

class TagGoogleCredentials(flask.json.tag.JSONTag):
    __slots__ = ('serializer',)
    
    key = 'gcred'

    def check(self, value):
        return isinstance(value, google.oauth2.credentials.Credentials)

    def to_json(self, value):
        return {
            'token': value.token,
            'refresh_token': value.refresh_token,
            'token_uri': value.token_uri,
            'client_id': value.client_id,
            'client_secret': value.client_secret,
            'scopes': value.scopes,
        }

    def to_python(self, value):
        return google.oauth2.credentials.Credentials(**value)

def api_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if 'credentials' not in flask.session:
            return flask.redirect('login')

        api = GoogleAPI(flask.session['credentials'])
        return f(api, *args, **kwargs)

    return wrapped
