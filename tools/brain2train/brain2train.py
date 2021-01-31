# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import pickle
import json
import codecs
import getopt
"""
brain2train.py - a tool that converts 'brain'-data back to training format.

Written: 2017-08-07 10:20 CET, ISO
"""


try:
    options, arguments = getopt.getopt(sys.argv[1:], 'b:t:', ['brain-file', 'train-file'])
except getopt.GetoptError:
    help()
    sys.exit(1)

brainfile = None
trainfile = None

for opt, arg in options:
    if opt in ('-b', '--brain-file'):
        brainfile = arg
    elif opt in ('-t', '--train-file'):
        trainfile = arg

if brainfile == None or trainfile == None:
    help()
    sys.exit(1)

braindata = pickle.load(open(brainfile, 'rb'))

brainAnswers = braindata['answers']
brainQuestions = braindata['questions']
trainQuestions = []
dictionaryEntries = []
defaultAnswers = []
mcugAnswers = {}
for brainAnswer in brainAnswers:
    defaultAnswers.append(brainAnswer['answer'])
    dictionaryEntries.append(brainAnswer['answer'])
    mcugA = brainAnswer['mcugAnswers']
    if mcugA == []:
        mcugA = {}
    answerID = brainAnswer['id']
    mcugAnswers[str(answerID)] = mcugA
    for key in mcugA.keys():
        dictionaryEntries.append(mcugA[key])

for i, brainQuestion in enumerate(brainQuestions):
    answers = brainQuestion['answers']
    answerID = answers[0]
    del brainQuestion['answers']
    brainQuestion['answerID'] = int(answerID)
    if 'qType' not in brainQuestion.keys():
        brainQuestion['qType'] = 'e'
    if 'category' not in brainQuestion.keys():
        brainQuestion['category'] = 1
    brainQuestion['qID'] = i
    trainQuestions.append(brainQuestion)
    dictionaryEntries.append(brainQuestion['question'])

trainData = {'questions': trainQuestions, 'defaultAnswers': defaultAnswers, 'mcugAnswers': mcugAnswers}

json.dump(trainData, codecs.open(trainfile + '.json', 'w', 'utf-8'), indent=4)
pickle.dump(trainData, open(trainfile + '.pickle', 'wb'))
dictFile = codecs.open(trainfile + '.txt', 'w', 'utf-8')
for entry in dictionaryEntries:
    print(entry, file=dictFile)
dictFile.close()




