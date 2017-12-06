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
types = ['time', 'cadence', 'watts', 'heartrate', 'grade_smooth', 'velocity_smooth']

activity = client.get_activity(activity_id)

streams = client.get_activity_streams(
        activity_id, types=types, resolution='high')

grade = np.array(streams['grade_smooth'].data)
cadence = np.array(streams['cadence'].data)
watts = np.array(streams['watts'].data)
heartrate = np.array(streams['heartrate'].data)
velocity = np.array(streams['velocity_smooth'].data)

plt.figure()
plt.scatter(cadence, watts, c=grade, cmap='cool')
plt.xlabel('Cadence (RPM)')
plt.ylabel('Power (Watts)')
plt.colorbar(label='Grade (%)')
plt.autoscale(True, 'both', True)

plt.figure()
plt.scatter(watts, heartrate, c=grade, cmap='cool')
plt.xlabel('Power (Watts)')
plt.ylabel('Heart Rate (BPM)')
plt.colorbar(label='Grade (%)')
plt.autoscale(True, 'both', True)

plt.figure()
plt.scatter(velocity, cadence, c=grade, cmap='cool')
plt.xlabel('Velocity (m/s)')
plt.ylabel('Cadence (RPM)')
plt.colorbar(label='Grade (%)')
plt.autoscale(True, 'both', True)

from matplotlib.colors import LogNorm

plt.figure()
plt.hist2d(cadence, watts, bins=40, norm=LogNorm(), cmap='cool')
plt.xlabel('Cadence (RPM)')
plt.ylabel('Power (Watts)')
plt.colorbar(label='Frequency')

plt.figure()
plt.hist2d(watts, heartrate, bins=40, norm=LogNorm(), cmap='cool')
plt.xlabel('Power (Watts)')
plt.ylabel('Heart Rate (BPM)')
plt.colorbar(label='Frequency')

plt.show()


