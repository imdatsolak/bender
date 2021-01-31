# -*- encoding: utf-8 -*-
from __future__ import print_function
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import codecs
import re

filename = sys.argv[1]
lines = open(filename, 'r').readlines()
names = []
html = re.compile(r".*Name\=([^']+).*")
clean = re.compile(r'<[^>]*>')
clean2 = re.compile(r'<[^>]*')
clean3 = re.compile(r'.*>')
for line in lines:
    line = line.strip()
    if 'class="ellipsis' in line or ('a href="http://www.vorname.com/name' in line and 'class="fwbold' in line):
        line = clean.sub('', line)
        line = line.strip()
        if len(line)>0:
            names.append(line)

for l in names:
    print(l)

