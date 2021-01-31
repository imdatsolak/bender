# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
import os
import logging
import nltk.data
import codecs
import shutil
import pickle
import json
import getopt
import re
import csv


"""
            mail2train.py v1.0
            Copyright (c) 2019 Imdat Solak
            All Rights Reserved

This tool is used to convert CSV-Files into training-data format used by Julia.
Usage:
    mail2train.py -i <input-dir> -a <answers-dir> -o <output-directory> [-t]

Created: 2017-06-08 09:00 CET, Imdat Solak


"""
class QAManager:
    def __init__(self):
        self.headers = []
        self.defaultAnswers = []
        self.dictionaryEntries = []
        #
        # Question array is structure like this
        # questions = [
        #               { 
        #                   'qID': <questionID>,
        #                   'category' : <categoryID>,
        #                   'type' : <questionType>,
        #                   'question' : <questionText>,
        #                   'answerID': <defaultAnswerID>,
        #               }, ...
        #              ]
                            
        self.questions = []
        #
        # mcugAnswers is a complicated dictionary containing the answers 
        # specific to a client (M), channel (C), and user-group (UG)
        #
        # The structure is:
        # mcugAnswers = { 
        #                   '<defaultAnswerID>' :  {
        #                       'm1-c1-ug1' : <answerText>,
        #                       'm1-c1-ug2' : <answerText>,
        #                       ...
        #                       'mn-cm-ugx' : <answerText>
        #                   }, ...
        #               }
        self.mcugAnswers = {}
        self.begQuoteRemover = re.compile(r'^"')
        self.endQuoteRemover = re.compile(r'"$')
        self.answers = {}

    def _processDefaultAnswer(self, answerText):
        if answerText in self.defaultAnswers:
            return self.defaultAnswers.index(answerText)
        else:
            self.defaultAnswers.append(answerText)
            self.dictionaryEntries.append(answerText)
            return len(self.defaultAnswers) - 1

    def _processAnswerForMCUG(self, defaultAnswerID, mcug, answerText):
        if defaultAnswerID is not None:
            ignored, client, channel, userGroup = mcug.split('-')
            dictKey = client.lower() + '-' + channel.lower() + '-' + userGroup.lower()
            if str(defaultAnswerID) in self.mcugAnswers.keys():
                dAEntries = self.mcugAnswers[str(defaultAnswerID)]
            else:
                dAEntries = {}
            dAEntries[dictKey] = answerText
            self.dictionaryEntries.append(answerText)
            self.mcugAnswers[str(defaultAnswerID)] = dAEntries
            return dAEntries
        return None

    def readAnswers(self, answersDir):
        for root, dirs, files in os.walk(answersDir):
            for directory in dirs:
                self.answers[directory] = ''

            for filename in filter(lambda filename: filename.endswith('.txt'), files):
                filename = os.path.join(root, filename)
                contents = codecs.open(filename, 'r', 'utf-8').readlines()
                textBody = '\n'.join(contents)
                file_topic = os.path.basename(os.path.dirname(filename))
                self.answers[file_topic] = self._processDefaultAnswer(textBody)
                self.mcugAnswers[str(self.answers[file_topic])] = { 'm1-c1-u1': textBody}

    def processDirectory(self, inputDir, plainTextFormat):
        dupQuoteRemover = re.compile(r'""')
        self.questions = []
        count = 0
        print('Reading files from {}...'.format(inputDir))
        categories = {}
        if plainTextFormat:
            extension = '.txt'
        else:
            extension = '.json'
        for root, dirs, files in os.walk(inputDir):
            for i, directory in enumerate(dirs):
                categories[directory] = i

            for filename in filter(lambda filename: filename.endswith(extension), files):
                count += 1
                if count % 50 == 0:
                    print('FILE {:-5d}: {}'.format(count, filename), end='\r' )
                    sys.stdout.flush()
                newEntry = {}
                filename = os.path.join(root, filename)
                if plainTextFormat:
                    contents = codecs.open(filename, 'r', 'utf-8').readlines()
                else:
                    try:
                        mail = json.load(codecs.open(filename, 'r', 'utf-8'))
                    except:
                        print('Error decoding {} as json'.format(filename))
                        continue
                    contents = mail['body']

                body = '\n'.join(contents)
                file_topic = os.path.basename(os.path.dirname(filename))
                newEntry['category'] = categories[file_topic]
                newEntry['answerID'] = self.answers[file_topic]
                newEntry['question'] = body
                newEntry['qType'] = 'e'
                newEntry['qID'] = len(self.questions)
                self.questions.append(newEntry)
        print('\n')

    def saveData(self, out_dir, cleanHTML=False):
        print('Saving... ', end='')
        sys.stdout.flush()
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        finalData = {
                'questions': self.questions,
                'defaultAnswers': self.defaultAnswers,
                'mcugAnswers' : self.mcugAnswers
                }
        pickle.dump(finalData, open(os.path.join(outputdir, 'traindata.pickle'), 'wb'))
        json.dump(finalData, codecs.open(os.path.join(outputdir, 'traindata.json'), 'w', 'utf-8'), indent=4)
        trainDictFile = codecs.open(os.path.join(outputdir, 'traindata.txt'), 'w', 'utf-8')
        htmlCleaner = re.compile(r'<[^>]+>')
        for line in self.dictionaryEntries:
            if cleanHTML:
                line = htmlCleaner.sub('', line)
            print(line, file=trainDictFile)
        trainDictFile.close()
        print('done')



try:
    options, arguments = getopt.getopt(sys.argv[1:], 'i:o:a:t', ['input=', 'output=', 'answers='])
except getopt.GetoptError:
    print('Usage:')
    print('\tpython convert_csv.py -i <inputdir> -a <answersdir> -o <outputdir> [-t]')
    print()
    print('\t-i <inputdir>          Input directory containing the mail files in sub-directories')
    print('\t-a <answersdir>        Directory containing answers')
    print('\t-o <outputdir>         Output directory where converted files should be saved')
    print('\t-t                     Are input-mails in plain-text-format (default=NO, i.e. JSON-Format)?')
    sys.exit(2)

verbose = False
dump = False
outputdir = None
inputdir = None
answersdir = None
plainTextFormat = False
for opt, arg in options:
    if opt in ('-i', '--input'):
        inputdir = arg	
    elif opt in ('-a', '--answers'):
        answersdir = arg
    elif opt in ('-o', '--output'):
        outputdir = arg
    elif opt in ('-t'):
        plainTextFormat = True

print("============================ CSV Converter ==============================")
print("               v1.0b - Copyright (c) 2019 Imdat Solak")
print("           Written by: Imdat Solak (imdat@solak.de)")
print("=========================================================================")

if inputdir == None or outputdir == None or answersdir == None:
    print('Usage: convert_csv.py -i <inputfile> -a <answersdir> -o <outputdir>')
    sys.exit(1)

processor = QAManager()
processor.readAnswers(answersdir)
processor.processDirectory(inputdir, plainTextFormat)
processor.saveData(outputdir)
