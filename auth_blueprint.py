"""
Routes responsible for authorisation and integration with Google OAuth
"""

import os
import google_auth_oauthlib.flow
import googleapiclient.discovery

from flask import Blueprint, url_for, session, redirect, flash, request
from security import credentials_to_dict

PROJECT_DIR = os.path.dirname(__file__)
CLIENT_SECRETS_FILE = os.path.join(PROJECT_DIR, 'client_secret_701113834116-726adijgkns945m5l467eu\
6gu02lb18b.apps.googleusercontent.com.json')
SCOPES = ['profile']

auth = Blueprint('auth', __name__, template_folder='templates')


@auth.route('/login', methods=['GET'])
def login_route():
    """
    Redirects user to Google auth link
    """
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES)
    flow.redirect_uri = url_for('auth.oauth2callback', _external=True)

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true')

    session['state'] = state

    return redirect(authorization_url)


@auth.route('/logout', methods=['GET'])
def logout_route():
    """
    Cleansup credentials from session and
    as result user logged out
    """
    if 'credentials' in session:
        del session['credentials']
    flash('You logged out')
    return redirect(url_for('index_route'))


@auth.route('/oauth2callback')
def oauth2callback():
    """
    Handles callback call from google, and finished authorization,
    then retrieves user info and saves it into session till next login
    """
    # Specify the state when creating the flow in the callback so that it can
    # verified in the authorization server response.
    state = session['state']

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = url_for('auth.oauth2callback', _external=True)

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)

    # Store credentials in the session.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)

    # requesting user info
    service = googleapiclient.discovery.build('people', 'v1',
                                              credentials=credentials)
    result = service.people().get(resourceName='people/me',
                                  personFields='names,photos').execute()

    user_id = result['resourceName']
    user_name = result['names'][0]['displayName']
    user_photo = url_for('static', filename='images/no-profile-photo.svg')
    if len(result['photos']) > 0:
        user_photo = result['photos'][0]['url']

    # saving user info to session, to avoid requesting it again and again
    # will be updated on every login
    session['user_id'] = user_id
    session['user_name'] = user_name
    session['user_photo'] = user_photo

    return redirect(url_for('index_route'))
