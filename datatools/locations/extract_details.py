# -*- coding: utf-8 -*-
from __future__ import print_function
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import codecs
import re
import os
import json
import pickle
from progressbar import ProgressBar, Percentage, Bar, ETA, FormatLabel, AnimatedMarker

key_maps = {'landkreis': 'COUNTY', 'ortsname': 'LOCATION', 'COMMUNITY': 'COMMUNITY', 'AGS': 'AGS', 'longitude': 'LONGITUDE', 'postleitzahl': 'ZIP', 'bundesland': 'STATE', 'latitude': 'LATITUDE', 'autokennzeichen': 'CAR-PLATE', 'status': 'STATUS', 'postleitzahlen': 'ZIPs', 'telefonvorwahl': 'AREA-CODE'}
newlines = re.compile(r'<br />')
html = re.compile(r'<[^>]*>')
degrees = re.compile(r'&deg.*')
remove_blanks = re.compile(r' ')

def convert_file(filename):
    single_loc = None
    lines = codecs.open(filename, 'r', 'utf-8').readlines()
    for line in lines:
        line = line.strip()
        line = newlines.sub('\t', line)
        line = html.sub('', line)
        if line.startswith('Ortsname'):
            single_loc = {}
            entries = line.split('\t')
            for entry in entries:
                title = ''
                if ':' in entry:
                    try:
                        (title, value) = entry.split(':')
                    except:
                        continue
                    title = title.strip().lower()
                    value = value.strip()
                    if 'amtlicher gemeinde' in title:
                        title = 'AGS'
                    elif 'bergeordnet' in title:
                        title  = 'COMMUNITY'
                    if 'postleitzahlen' in title and len(value):
                        value = remove_blanks.sub('', value)
                        zip_codes = value.split(',')
                        value = zip_codes
                    if len(value):
                        if title in key_maps:
                            title = key_maps[title]
                            single_loc[title] = value
                elif 'Latitude' in entry or 'Longitude' in entry:
                    (title, value) = entry.split('(')
                    if 'Latitude' in title:
                        title = 'LATITUDE'
                    else:
                        title = 'LONGITUDE'
                    value = value.strip()
                    value = degrees.sub('', value)
                    if len(value):
                        single_loc[title] = value
                if title == 'LONGITUDE':
                    break
    return single_loc



all_locations = {}
top_directory = 'community/'
for root, dirs, files in os.walk(top_directory):
    files.sort()
    widgets=[FormatLabel('File: %(message)s [%(value)s/'+str(len(files))+']'), ' ', Percentage(), ' ', Bar(marker='@', left='[', right=']'    ), ' ', ETA()]
    counter = 0
    pBar = ProgressBar(widgets=widgets, maxval=len(files)).start()
    for filename in filter(lambda filename: filename.endswith('.html'), files):
        counter += 1
        pBar.update(counter, filename)
	filename = os.path.join(root, filename)
        one_loc = convert_file(filename)
        if one_loc != None:
            all_locations[one_loc['LOCATION']] = one_loc

    pBar.finish()
print('\nSaving...', end='')
sys.stdout.flush()
json.dump(all_locations, codecs.open('all_locations.json', 'w', 'utf-8'), indent=4)
pickle.dump(all_locations, open('all_locations.pickle', 'wb'))
print(' done')
