#!/usr/bin/env python2.7

# /dev/disk/by-id/usb-Garmin_Edge_800_Flash_0000e52fb239-0:0

# upload-gpx-tracks.py - upload latest GPX tracks from a Garmin device
# to Strava http://strava.com using Strava API
# It is meant to be automatically run on each USB storage device attachment.
# Usage: upload-gpx-tracks.py <device>
#
# Copyright (C) 2015 Grigory Rechistov
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# This script reuses code from stravaup.py from 
# https://github.com/dlenski/stravacli . It uses the same authorization token
# acquisition procedure, described at
# https://github.com/dlenski/stravacli#application-authorization, and shares it
# with stravacli ($HOME/.stravacli)

# Other dependedncies:
# - stravalib from https://github.com/hozn/stravalib
# - Dbus bindings for desktop notifications, device mounting etc.
from __future__ import print_function

import sys
import datetime
import os, stat
from subprocess import call as call

# Original stravaup.py imports
from stravalib import Client, exc
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

import dbus
import gobject
from dbus.mainloop.glib import DBusGMainLoop

def popup(msg):
    print (msg)
    notify = bus.get_object('org.freedesktop.Notifications',
                            '/org/freedesktop/Notifications')
    method = notify.get_dbus_method('Notify', 'org.freedesktop.Notifications')
    method(sys.argv[0], # app_name
           0,           # replaces_id
           "",          # app_icon
           "Upload to Strava", # summary
           msg, # body
           [],  # actions
           [],  # hints
           -1)   # expire_timeout

def usage():
    print ("Usage: %s <device>" % sys.argv[0], file = sys.stderr)
    print ("For getting Strava API authorization token, see" \
           " https://github.com/dlenski/stravacli#application-authorization",
           file = sys.stderr)
    exit(1)

def upload_activities(activities):
    if len(activities) == 0:
        print("No new activities")
        return True
    cid = 3163 # CLIENT_ID from stravacli
    cp = ConfigParser.ConfigParser()
    cp.read(os.path.expanduser(configfilename))
    try: cat = cp.get('API', 'ACCESS_TOKEN')
    except:
        popup("Cannot find access_token in %s" % configfilename)
        return False

    client = Client(cat)
    try:
        athlete = client.get_athlete()
    except requests.exceptions.ConnectionError:
        popup("Could not connect to Strava API")
        return False
    except Exception as e:
        popup("Not authorized at Strava")
        print("To get authorization, see"
              " https://github.com/dlenski/stravacli#application-authorization",
              file=stderr)
        return False

    print("Welcome {} {} (id {:d}).".format(athlete.firstname,
                                            athlete.lastname, athlete.id))
    for f in activities:
        base, ext = os.path.splitext(f)
        cf =  NamedTemporaryFile(suffix='.gz')
        gzip.GzipFile(fileobj=cf, mode='w+b').writelines(open(f, "rb"))
        print("Uploading activity from {}...".format(f))

        title = None
        desc = "Uploaded automatically using https://github.com/hozn/stravalib"

        # Upload compresed activity
        try:
            cf.seek(0, 0)
            upstat = client.upload_activity(cf, ext[1:] + '.gz',
                                            title,
                                            desc,
                                            private=True)
                                            # TODO detect activity_type somehow?
            activity = upstat.wait()
            duplicate = False
        except exc.ActivityUploadFailed as e:
            words = e.args[0].split()
            if words[-4:-1]==['duplicate','of','activity']:
                activity = client.get_activity(words[-1])
                #popup(f + ": duplicate")
                duplicate = True
            else:
                popup(f + ": " + e.args[0])
                return False

        # Show results as URL and open in browser
        uri = "http://strava.com/activities/{:d}".format(activity.id)
        popup("{}{}".format(uri, " (duplicate)" if duplicate else ''))
        webbrowser.open_new_tab(uri)
    return True

def detect_sesion_bus():
    # Look for a file inside .dbus/session-bus/ directory
    # and extract DBUS_SESSION_BUS_ADDRESS from its contents.
    topfolder = os.path.expanduser("~/.dbus/session-bus")
    for dirpath, dirs, fnames in os.walk(topfolder):
        for fname in fnames:
            fname = os.path.join(dirpath, fname)
            lines = open(fname, "r").readlines()
            for l in lines:
                if l[0] == '#': continue
                l = l.strip().split("=", 1) # Split on the first '='
                if l[0] == "DBUS_SESSION_BUS_ADDRESS":
                    return l[1]
    raise Exception("Failed to detect DBUS_SESSION_BUS_ADDRESS")
    
### Configuration
configfilename = '~/.stravacli'
size_threshold = 1*1024

### Main code

# The script is often started from a headless environment, unaware of any
# X11 or DBus. While X11 is used only to show nice notifications,
# the DBus dependedncy is essential as it does privileged mounting operations.
# For things to work, a session bus has to be known, system bus cannot be
# used instead.
# TODO Make the script work even in absense of X display.
if not os.environ.has_key("DISPLAY"):
    os.environ['DISPLAY'] = ":0"
if not os.environ.has_key("DBUS_SESSION_BUS_ADDRESS"):
    os.environ['DBUS_SESSION_BUS_ADDRESS'] = detect_sesion_bus()

sysbus = dbus.SystemBus()
bus = dbus.SessionBus()

devname = '/dev/null'
try: mountpoint = sys.argv[1]
except: usage()

print("Started: " + datetime.datetime.today().strftime("%s") + " " + devname)

# If required, extract the last part of the device name, "/dev/sdb" -> "sdb"
devname = devname.split("/")[-1]

# Mount the device
udisk = sysbus.get_object("org.freedesktop.UDisks",
                          "/org/freedesktop/UDisks/devices/%s" % devname)
mount = udisk.get_dbus_method("FilesystemMount",
                              dbus_interface="org.freedesktop.UDisks.Device")
unmount = udisk.get_dbus_method("FilesystemUnmount",
                                dbus_interface="org.freedesktop.UDisks.Device")

# The line below tests notification mechanism before doing any mounting.
# If we fail here, at least the device will not be touched.
#popup("Mounting %s" % (devname))
#try: mountpoint = mount("", # fstype
#                        dbus.Array([], signature="s")) # options
#except:
#    popup("Failed to mount %s" % devname)
#    raise

# Get a list of all new GPX files since last sync time
cp = ConfigParser.ConfigParser()
cp.read(os.path.expanduser(configfilename))
if cp.has_section('UPLOAD') and 'last_time' in cp.options('UPLOAD'):
    last_time = int(cp.get('UPLOAD', 'last_time'))
else: last_time = 0

# Root directory where GPX files are placed on Garmin devices
gpx_root = mountpoint + "/Garmin/Activities/"

upload_list = []
for dirpath, dirnames, filenames in os.walk(gpx_root):
    for fname in filenames:
        if os.path.splitext(fname)[1].lower() == ".fit":
            fname = os.path.join(dirpath, fname)
            fstats = os.stat(fname)
            mtime = fstats.st_mtime
            size  = fstats.st_size

            if (last_time > mtime): continue
            if (size < size_threshold):
                print ("New GPX '%s' size is below threshold, ignored" % fname)
                continue
            print ("New GPX '%s', mtime %s, size %d" % (fname, mtime, size))
            upload_list.append(fname)

print ("List of GPX to upload: ", upload_list)
 
# Upload new GPX files
result = upload_activities(upload_list)
if not result:
    popup("One or more GPX files failed to upload")
else:
    # Record the last sync time to prevent submission of duplicates next time
    last_time = datetime.datetime.today().strftime("%s")
    if not cp.has_section('UPLOAD'):
        cp.add_section('UPLOAD')
    cp.set('UPLOAD', 'last_time', last_time)
    cp.write(open(os.path.expanduser(configfilename),"w"))

# Unmount the device
#try:
    #call(['sync']) # Wait for FS to become ready
    #unmount(dbus.Array(["force"], signature="s"))
    #popup("%s is unmounted" % mountpoint)
#except:
    #popup("Failed to unmount the file system, it is probably busy")
    #raise
exit(0)
