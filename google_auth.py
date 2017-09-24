#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module contains some auxiliary functions for
implementing the Google Plus authentication scenario
"""
import json
import random
import string
from flask import make_response
import httplib2
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import requests


# Some helper functions for Google authentication
# Make a JSON response with a message and code
def make_json_response(message, code):
    response = make_response(json.dumps(message), code)
    response.headers['Content-Type'] = 'application/json'
    return response


# Generate a random state token
def generate_state_token():
    return ''.join(random.choice(string.ascii_uppercase + string.digits)
                   for x in range(32))


# Get Google credentials using an authentication code and a secrets file
def get_credentials(auth_code, client_secrets_file):
    try:
        oauth_flow = flow_from_clientsecrets(client_secrets_file, scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(auth_code)
    except FlowExchangeError:
        return None

    return credentials


# Check if Google credetials are valid and ok
def check_credentials(credentials, CLIENT_ID):
    res = {}

    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % credentials.access_token)
    h = httplib2.Http()
    content = (h.request(url, 'GET')[1]).decode('utf-8')
    result = json.loads(content)

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        res = dict(message=result.get('error'), code=500)
        return res

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        res = dict(message="Token's user ID doesn't match given user ID.",
                   code=401)
        return res

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        res = dict(message="Token's client ID does not match app's.",
                   code=401)
        return res

    return res


# Obtain the name and email address of a Google Plus user
def get_user_name_and_email(credentials):

    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = answer.json()
    return data['name'], data['email']


# Revoke the access granted earlier by Google Plus
def revoke_access(access_token):

    url = "https://accounts.google.com/o/oauth2/revoke?token=%s" % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        return True
    else:
        return False
