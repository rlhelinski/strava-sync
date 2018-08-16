#!/usr/bin/env python2.7

from __future__ import print_function

import sys
import datetime
import os, stat
from subprocess import call as call

# Original stravaup.py imports
from stravalib import Client, exc, unithelper
from sys import stderr, stdin, exit
from tempfile import NamedTemporaryFile
import webbrowser, os.path, gzip
try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser
import argparse
import requests
try:
    from lxml import etree
except ImportError:
    import xml.etree.ElementTree as etree

def secs_to_days(secs):
    return secs/60/60/24

### Configuration
configfilename = '~/.stravacli'

cp = ConfigParser()
cp.read(os.path.expanduser(configfilename))
try: cat = cp.get('API', 'ACCESS_TOKEN')
except:
    popup("Cannot find access_token in %s" % configfilename)
    sys.exit(-1)

client = Client(cat)

gear_max_speed = {}
gear_activity = {}


for activity in client.get_activities():
    if activity.type != 'Ride':
        continue
    
    if activity.gear_id not in gear_max_speed or \
        gear_max_speed[activity.gear_id] < activity.max_speed:
        gear_max_speed[activity.gear_id] = activity.max_speed
        gear_activity[activity.gear_id] = activity.id


    if activity.flagged:
        print ('Activity %d is flagged' % activity.id)


gear_details = {}
for gear_id in gear_max_speed.keys():
    if not gear_id:
        continue
    gear_details[gear_id] = client.get_gear(gear_id)


for gear_id, details in gear_details.items():
    print (details.name,
        unithelper.miles_per_hour(gear_max_speed[gear_id]),
        gear_activity[gear_id])

athlete = client.get_athlete()

# also convert to JSON for external prototyping
json_obj = {
        'date': datetime.datetime.now().ctime(),
        'gear': {},
        'athelete': {
            'id': athlete.id,
            'lastname': athlete.lastname,
            'firstname': athlete.firstname
            },
        }

for gear_id, details in gear_details.items():
    json_obj['gear'][gear_id] = {
        'name': details.name,
        'max_speed': str(unithelper.miles_per_hour(gear_max_speed[gear_id])),
        'activity_id': gear_activity[gear_id]
    }

import json
fp = open('max_speeds.json', 'w')
json.dump(json_obj, fp, sort_keys=True, indent=4, separators=(', ', ': '))
fp.close()
