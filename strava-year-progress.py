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
import webbrowser, os.path, ConfigParser, gzip
import argparse
from cStringIO import StringIO
import requests
try:
    from lxml import etree
except ImportError:
    import xml.etree.ElementTree as etree

### Configuration
configfilename = '~/.stravacli'

cp = ConfigParser.ConfigParser()
cp.read(os.path.expanduser(configfilename))
try: cat = cp.get('API', 'ACCESS_TOKEN')
except:
    popup("Cannot find access_token in %s" % configfilename)
    sys.exit(-1)

client = Client(cat)

years = {}

origin_year = datetime.datetime.now().year-3

for activity in client.get_activities(
        after='%d-01-01T00:00:00Z' % origin_year
        ):
    if activity.type != 'Ride':
        continue
    if activity.start_date.year not in years:
        years[activity.start_date.year] = {
                'datetime': [],
                'distance': []
                }

    years[activity.start_date.year]['datetime'].append(activity.start_date)
    years[activity.start_date.year]['distance'].append(
            unithelper.miles(activity.distance).num)

# Sort each year's activities
# Create parametric vectors for each year
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.dates import date2num

athlete = client.get_athlete()

# also convert to JSON for external prototyping
json_obj = {
        'date': datetime.datetime.now().ctime(),
        'years': {},
        'athelete': {
            'id': athlete.id,
            'lastname': athlete.lastname,
            'firstname': athlete.firstname
            },
        }

for year in sorted(years.keys()):
    origin = datetime.datetime(year, 1, 1)
    days_of_year = np.array([(dt.replace(tzinfo=None) - origin).total_seconds() for dt in years[year]['datetime']])/60/60/24
    distances = np.cumsum(years[year]['distance'])
    plt.plot(days_of_year, distances, label='%d' % year)
    json_obj['years'][year] = {}
    json_obj['years'][year]['days'] = days_of_year.tolist()
    json_obj['years'][year]['distances'] = distances.tolist()

plt.xlim(0, 366)
plt.xlabel('Days of the Year')
plt.ylabel('Cumulative Miles')
plt.title('Annual Distance for %s %s (%d)' % (athlete.firstname, athlete.lastname, athlete.id))
plt.legend(loc='best')
plt.show()

import json
fp = open('data.json', 'w')
json.dump(json_obj, fp)
fp.close()
