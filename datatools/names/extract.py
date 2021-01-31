# -*- encoding: utf-8 -*-
from __future__ import print_function
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import codecs

filename = sys.argv[1]

lines = codecs.open(filename, 'r', 'utf-8').readlines()
beg_found = False
names = []
for line in lines:
    line = line.strip()
    if line == '<div class="nam">':
        beg_found = True
        continue
    elif line == '</div>' and beg_found == True:
        break
    if beg_found:
        nl = line.split()
        names.extend(nl)


for n in names:
    print(n)

