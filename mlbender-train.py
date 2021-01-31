# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
import os
import logging
import nltk.data
import random
import getopt
from core import utils
from training.trainingdata import TrainingDataConverter

random.seed(42)
"""
Bender training tool

Usage:
    python bender-train.py -c config-file
 
Copyright (c) 2019 Imdat Solak
              All Rights Reserved.
"""

configFile = ''
try:
    options, arguments = getopt.getopt(sys.argv[1:], 'dhc:vV', ['dump', 'help', 'config=', 'version', 'verbose'])
except getopt.GetoptError:
    print('Usage:')
    print('\tpython bender-train.py [-h|--help] [-v|--version] [-V|--verbose]  [-d|--dump] -c|--config <config-file>')
    print("\tPlease use '-d' (debug-mode) only during development!!")
    sys.exit(2)

verbose = False
dump = False
for opt, arg in options:
    if opt == '-h':
        print('No Help yet')
        sys.exit(0)
    elif opt in ('-v', '--version'):
        print("V1.0beta")
        sys.exit(0)
    elif opt in ('-c', '--config'):
        configFile = arg
    elif opt in ('-V', '--verbose'):
        verbose = True
    elif opt in ('-d', '--dump'):
        dump = True
print("============================ Bender Trainer ==============================")
print("           Bender 2.0a - Copyright (c) 2019 Imdat Solak")
print("           Written by: Imdat Solak (imdat@solak.de)")
print("=========================================================================")

benderConfig = utils.getBenderConfiguration(configFile, verbose, False)
logger = logging.getLogger(os.path.basename(sys.argv[0]))
logFile = utils.getKeyFromSectionInConfiguration('bender-training', 'train_log_file', 'logs/bender-train.log', benderConfig)
utils.safe_create_directory(os.path.dirname(logFile))
logging.basicConfig(filename=logFile, format='%(asctime)s: %(levelname)s: %(message)s')
logging.root.setLevel(level=logging.INFO)
logger.info('**************** NEW TRAINING SESSION STARTED: %s' % ' '.join(sys.argv))
tdc = TrainingDataConverter(benderConfig)
tdc.train()
