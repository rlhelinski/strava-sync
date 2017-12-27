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

def smooth(x,window_len=11,window='hanning'):
    """smooth the data using a window with requested size.

    This method is based on the convolution of a scaled window with the signal.
    The signal is prepared by introducing reflected copies of the signal
    (with the window size) in both ends so that transient parts are minimized
    in the begining and end part of the output signal.

    input:
        x: the input signal
        window_len: the dimension of the smoothing window; should be an odd integer
        window: the type of window from 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'
            flat window will produce a moving average smoothing.

    output:
        the smoothed signal

    example:

    t=linspace(-2,2,0.1)
    x=sin(t)+randn(len(t))*0.1
    y=smooth(x)

    see also:

    numpy.hanning, numpy.hamming, numpy.bartlett, numpy.blackman, numpy.convolve
    scipy.signal.lfilter

    TODO: the window parameter could be the window itself if an array instead of a string
    NOTE: length(output) != length(input), to correct this: return y[(window_len/2-1):-(window_len/2)] instead of just y.
    """

    if x.ndim != 1:
        raise ValueError, "smooth only accepts 1 dimension arrays."

    if x.size < window_len:
        raise ValueError, "Input vector needs to be bigger than window size."


    if window_len<3:
        return x


    if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
        raise ValueError, "Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'"


    s=np.r_[x[window_len-1:0:-1],x,x[-2:-window_len-1:-1]]
    #print(len(s))
    if window == 'flat': #moving average
        w=np.ones(window_len,'d')
    else:
        w=eval('np.'+window+'(window_len)')

    y=np.convolve(w/w.sum(),s,mode='valid')
    return y


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
print(grade.shape)
grade = smooth(grade, 41, 'flat')[:-40]
print(grade.shape)
cadence = np.array(streams['cadence'].data)
watts = np.array(streams['watts'].data)
heartrate = np.array(streams['heartrate'].data)
velocity = np.array(streams['velocity_smooth'].data)

plt.figure()
plt.scatter(cadence, watts, c=grade, cmap='cool')
plt.xlabel('Cadence (RPM)')
plt.ylabel('Power (Watts)')
plt.title('Activity %d' % activity_id)
plt.colorbar(label='Grade (%)')
plt.autoscale(True, 'both', True)
plt.savefig('power_vs_cadence.png')

plt.figure()
plt.scatter(watts, heartrate, c=grade, cmap='cool')
plt.xlabel('Power (Watts)')
plt.ylabel('Heart Rate (BPM)')
plt.title('Activity %d' % activity_id)
plt.colorbar(label='Grade (%)')
plt.autoscale(True, 'both', True)
plt.savefig('heartrate_vs_power.png')

plt.figure()
plt.scatter(velocity, cadence, c=grade, cmap='cool')
plt.xlabel('Velocity (m/s)')
plt.ylabel('Cadence (RPM)')
plt.title('Activity %d' % activity_id)
plt.colorbar(label='Grade (%)')
plt.autoscale(True, 'both', True)
plt.savefig('cadence_vs_velocity.png')

from matplotlib.colors import LogNorm

plt.figure()
plt.hist2d(cadence, watts, bins=40, norm=LogNorm(), cmap='cool')
plt.xlabel('Cadence (RPM)')
plt.ylabel('Power (Watts)')
plt.title('Activity %d' % activity_id)
plt.colorbar(label='Frequency')
plt.savefig('histogram_cadence_and_power.png')

plt.figure()
plt.hist2d(watts, heartrate, bins=40, norm=LogNorm(), cmap='cool')
plt.xlabel('Power (Watts)')
plt.ylabel('Heart Rate (BPM)')
plt.title('Activity %d' % activity_id)
plt.colorbar(label='Frequency')
plt.savefig('histogram_power_and_heartrate.png')

plt.show()


