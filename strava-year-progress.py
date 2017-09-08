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
    years[activity.start_date.year]['distance'].append(activity.distance)

# Sort each year's activities
# Create parametric vectors for each year
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.dates import date2num


fig, ax = plt.subplots()
for year in sorted(years.keys()):
    origin = datetime.datetime(year, 1, 1)
    days_of_year = [(dt.replace(tzinfo=None) - origin).total_seconds() for dt in years[year]['datetime']]
    plt.plot(
            days_of_year,
            np.cumsum(years[year]['distance']),
            label='%d' % year
            )
labels = ax.get_xticklabels()
plt.setp(labels, rotation=45)
plt.legend(loc='best')
plt.show()

import pdb; pdb.set_trace()

curves = {}
for year, activities in years.items():
    #years[year] = sorted(years[year], key=lambda t: t[0])
    curves[year] = np.zeros((len(activities), 2))
    #curves[year][:, 0] = 

