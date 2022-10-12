# test_pyensemble_connect.py

import os
import requests
import re

from configparser import ConfigParser

import pdb

PASS_DIR = os.environ['HOME']

config = ConfigParser()
config.read(os.path.join(PASS_DIR, 'pyensemble_params.ini'))

server = config['pyensemble']['server']
user = config['pyensemble']['user']
password = config['pyensemble']['password']

session_url = server + '/group/session/attach/experimenter/'

# Create a session object
s = requests.Session()

# Get the form we need to complete
resp = s.get(session_url)

# Check whether it is a login form
p = re.compile('name="username"')
match = p.search(resp.text)

if match:
    # Login and redirect to session_url
    resp = s.post(resp.url, {'username': user, 'password':password, 'csrfmiddlewaretoken': s.cookies['csrftoken']})

# Check whether we are being prompted for the experimenter code
p = re.compile('name="experimenter_code"')
match = p.search(resp.text)

if match:
    # Get the experimenter code from our value field
    experimenter_code = 'f305'
    resp = s.post(session_url, {'experimenter_code': experimenter_code, 'csrfmiddlewaretoken': s.cookies['csrftoken']})
