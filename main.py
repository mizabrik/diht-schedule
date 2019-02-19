# -*- coding: utf-8 -*-

import os

import flask
import googleapiclient.discovery

from google_api import GoogleAPI, TagGoogleCredentials, api_required
from forms import LoginForm, LogoutForm, ScheduleSettingsForm
import subjects


app = flask.Flask(__name__)

app.secret_key = os.environ['FLASK_SECRET_KEY']
app.jinja_env.filters['zip'] = zip
app.session_interface.serializer.register(TagGoogleCredentials)


@app.route('/')
@api_required
def index(api):
    if 'credentials' not in flask.session:
        return flask.render_template('authorize.html', form=LoginForm())

    api = GoogleAPI(flask.session['credentials'])
  
    email = api.get_user_email()

    schedule_form = ScheduleSettingsForm()
    schedule_form.existing_calendar.choices = api.get_writable_calendars()

    return flask.render_template(
            'main.html', email=email,
            logout_form=LogoutForm(), schedule_form=schedule_form)

@app.route('/create_schedule', methods=('POST',))
@api_required
def create_schedule(api):
    form = ScheduleSettingsForm()
    form.existing_calendar.choices = api.get_writable_calendars()

    if not form.validate_on_submit():
        return flask.render_template('main.html', schedule_form=form)
        return flask.redirect('/')

    if form.create_calendar.data:
        calendar = api.create_calendar(form.new_calendar.data)
    else:
        calendar = form.existing_calendar.data

    events = []
    def add_events(es):
        for e in es:
            e = e.copy()
            if 'alt_summary' in e:
                if form.use_alt_name.data:
                    e['summary'] = e['alt_summary']
                del e['alt_summary']
            events.append(e)

    if form.obligatory.data:
        add_events(subjects.obligatory)
    for group, electives in form.electives.data.items():
        for elective in electives:
            add_events(subjects.electives[elective])

    api.create_events(calendar, events)

    return flask.redirect('/success')

@app.route('/success')
def success():
    return flask.render_template('success.html')

@app.route('/login', methods=('GET', 'POST',))
def login():
    form = LoginForm()
    if not form.validate_on_submit():
        return flask.render_template('login.html', form=LoginForm())

    auth_url, state = GoogleAPI.get_authentication_url(
            flask.url_for('oauth2callback', _external=True))
    flask.session['state'] = state

    return flask.redirect(auth_url)

@app.route('/oauth2callback')
def oauth2callback():
    flask.session['credentials'] = GoogleAPI.process_authentication_response(
            flask.request.url,
            flask.session['state'],
            flask.url_for('oauth2callback', _external=True))
  
    return flask.redirect(flask.url_for('index'))

@app.route('/logout', methods=('POST',))
def logout():
    form = LogoutForm()
    if not form.validate_on_submit():
        return redirect('/')

    if 'credentials' not in flask.session:
      return 'Нет привязанного Google аккаунта'

    revoke = GoogleAPI.revoke_token(flask.session['credentials'])
    del flask.session['credentials']

    status_code = getattr(revoke, 'status_code')
    if status_code == 200:
        return flask.redirect('/')
    else:
        return 'Произошла ошибка: ' + revoke.text

if __name__ == '__main__':
    # Used only for local runs.
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.run('localhost', 8080, debug=True)
