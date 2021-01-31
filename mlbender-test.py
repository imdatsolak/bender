# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
import os
import ConfigParser
import logging
import getopt
import random
import codecs
# FLASK Related imports
import json

# BENDER Core Import - Bender Core is the class that does the actual job
from core.bendercore import BenderCore
from core import utils

random.seed(42)
"""
This file contains Bender's main code to run tests.
For training, use "bender-train.py"

Bender requires a configuration file and you must provide the full-path to the configuration file.
The configuration file defines certain parameters of Bender. 

Usage:
    python mlbender-test.py -c <config-file> -t <test-file>
 
Copyright (c) 2019 Imdat Solak
              All Rights Reserved.
 
Created: 2018-02-14 12:55 CET, ISO

"""

BENDER_VERSION = "2.0b"
BENDER_FULL_VERSION = "MLBender (NATHAN)" + BENDER_VERSION
# Our API endpoints all start with this ...

configFile = ''
testFile = None
try:
    options, arguments = getopt.getopt(sys.argv[1:], 'c:t:', ['config', 'test'])
except getopt.GetoptError:
    print('Usage:')
    print('\tpython mlbender-test.py -t|--test <test-file> -c|--config <config-file>')
    sys.exit(2)

for opt, arg in options:
    if opt in ('-c', '--config'):
        configFile = arg
    elif opt in ('-t', '--test'):
        testFile = arg

try:
    benderConfig = utils.getBenderConfiguration(configFile, False, False)
except:
    print('ERROR: Cannot load configFile %s' % os.path.join(os.getcwd(), configFile))
    sys.exit(1)

benderConfig['bender-core']['version'] = BENDER_VERSION
print('' + BENDER_FULL_VERSION +' - Copyright (c) 2019 Imdat Solak')
print('        Written by: Imdat Solak (imdat@solak.de)')
print('=========================================================================')
print('INFO: Interactive mode ... NOT using HLI & NOT using LOOKUP...')
print('Loading application, please wait...')

benderConfig['bender-core']['interactive'] = 1
benderConfig['bender-core']['use_hli'] = 0
benderConfig['bender-core']['use_lookup'] = 0
benderCore = BenderCore(benderConfig)
print('Performing tests...')
test_data_file = codecs.open(testFile, 'r', 'utf-8')
test_log_filename = testFile + '_test.log'
print('Writing test log to {}'.format(test_log_filename))
log_file = codecs.open(test_log_filename, 'w', 'utf-8')
for i, line in enumerate(test_data_file):
    line = line.strip()
    question, answer = line.split('\t')
    requestData = {
            'clientID': 'batchTestClient', 
            'queryText': question,
            'queryInputType': 'text',
            'requestedResponseType': 'text'
        }
    result, resCode = benderCore.performRequest(requestData)
    if resCode == 200:
        result_str = json.dumps(result)
        print('{}:{}'.format(i, result_str), file=log_file)
    else:
        print('{}: ERROR {}'.format(i, resCode), file=log_file)

test_data_file.close()
log_file.close()

os._exit(0)
