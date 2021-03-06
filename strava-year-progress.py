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

def secs_to_days(secs):
    return secs/60/60/24

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

last_n_years = 5
origin_year = datetime.datetime.now().year-last_n_years

for activity in client.get_activities(
        after='%d-01-01T00:00:00Z' % origin_year
        ):
    if activity.type != 'Ride':
        continue
    if activity.start_date.year not in years:
        years[activity.start_date.year] = {
                'datetime': [],
                'elevation_gain': [],
                'distance': []
                }

    years[activity.start_date.year]['datetime'].append(activity.start_date)
    years[activity.start_date.year]['distance'].append(
            unithelper.miles(activity.distance).num)
    years[activity.start_date.year]['elevation_gain'].append(
            unithelper.feet(activity.total_elevation_gain).num)

    if activity.flagged:
        print ('Activity %d is flagged' % activity.id)

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

max_cumul_dist = 0
for year in sorted(years.keys()):
    origin = datetime.datetime(year, 1, 1)
    days_of_year = secs_to_days(np.array([(dt.replace(tzinfo=None) - origin).total_seconds() for dt in years[year]['datetime']]))
    distances = np.cumsum(years[year]['distance'])
    elev_gains = np.cumsum(years[year]['elevation_gain'])
    max_cumul_dist = max(max_cumul_dist, distances[-1])
    plt.figure(1)
    plt.plot(days_of_year, distances, label='%d' % year)
    plt.figure(2)
    plt.plot(days_of_year, elev_gains/1000, label='%d' % year)
    json_obj['years'][year] = {}
    json_obj['years'][year]['days'] = days_of_year.tolist()
    json_obj['years'][year]['distances'] = distances.tolist()
    json_obj['years'][year]['elevation_gains'] = elev_gains.tolist()
    print ('Year %d total distance: %.2f miles, total elevation gain: %.2f feet' % (year, distances[-1], elev_gains[-1]))

plt.figure(1)
plt.xlim(0, 366)
plt.xlabel('Days of the Year')
plt.ylabel('Cumulative Miles')
plt.title('Annual Distance for %s %s (%d)' % (athlete.firstname, athlete.lastname, athlete.id))
plt.legend(loc='best')
# make vertical lines for each month
for mi in range(1, 13):
    plt.axvline(secs_to_days((datetime.datetime(2017, mi, 1) - origin).total_seconds()), c='gray', ls='dotted')
# make horizontal lines for each 1,000 miles
for ti in range(1, int(max_cumul_dist/1000)+1):
    plt.axhline(ti*1000, c='gray', ls='dotted')

plt.figure(2)
plt.xlim(0, 366)
plt.xlabel('Days of the Year')
plt.ylabel('Cumulative Elevation Gain (1,000 feet)')
plt.title('Annual Elevation Gain for %s %s (%d)' % (athlete.firstname, athlete.lastname, athlete.id))
plt.legend(loc='best')
# make vertical lines for each month
for mi in range(1, 13):
    plt.axvline(secs_to_days((datetime.datetime(2017, mi, 1) - origin).total_seconds()), c='gray', ls='dotted')
# make horizontal lines for each 100,000 feet
for ti in range(1, int(max_cumul_dist/1000)+1):
    plt.axhline(ti*100, c='gray', ls='dotted')

plt.show()

import json
fp = open('data.json', 'w')
json.dump(json_obj, fp, sort_keys=True, indent=4, separators=(', ', ': '))
fp.close()
