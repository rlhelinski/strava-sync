"""
This script fetches an activity and plots some interesting plots for
performance analysis.
"""

from __future__ import print_function

import sys

# Original stravaup.py imports
from stravalib import Client
import os.path, ConfigParser
import argparse

import numpy as np
import matplotlib.pyplot as plt

def secs_to_days(secs):
    "Convert seconds into days"
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

activity_id = 1301160092
types = ['time', 'cadence', 'watts', 'heartrate']

activity = client.get_activity(activity_id)

streams = client.get_activity_streams(
        activity_id, types=types, resolution='high')

plt.figure()
plt.plot(streams['cadence'].data, streams['watts'].data, '.')
plt.xlabel('Cadence (RPM)')
plt.ylabel('Power (Watts)')

plt.figure()
plt.plot(streams['watts'].data, streams['heartrate'].data, '.')
plt.xlabel('Power (Watts)')
plt.ylabel('Heart Rate (BPM)')

plt.show()


