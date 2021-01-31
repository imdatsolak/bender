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
                csv2train.py v1.0

This tool is used to convert CSV-Files into training-data format used by Bender.
Usage:
    csv2train.py -i <input-csv-file> -o <output-directory>

Created: 2017-06-08 09:00 CET, Imdat Solak

RULES:
    - The CSV-File *must* be semicolon (;)-delimited.
    - The CSV-file *must* be UTF-8
    - The first row *must* be the title row
    - The first answer-column *must* be the DEFAULT-ANSWER-COLUMN!!!
    - Column-titles allowed/understood:
        - Category
        - Type
        - Question
        - Answer
        - A-Mn-Cm-UGx (Answer for Client /n/ (M), Channel /m/, and UserGroup /x/)

NOTES: PLEASE READ THE README.md in this directory!!!

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


    def _processSingleLine(self, columns):
        """
        This method reads a line from the csv-file (in memory)
        and does the following:
        QUESTION: 
            - remove all punctuation
            - lowercase all text
            - remove all special characters
            - if necessary, convert to UTF-8
            - save in 'self.questions'
            - one day, in future: lemmatize the text :-)
        ANSWERS:
            - cleanup
            - check if answer already exists
                - if so, save the existingAnswerID as answer to question
                - if not, create new answerID as answer to question
            - The above process is done for each answer-type (default as well as Client/Channel/UG-Specific)
            - The answer array 
        """
        newEntry = {}
        category = None
        qType = None
        question = None
        defaultAnswerID = None

        for i, entry in enumerate(columns):
            entry = unicode(entry, 'utf-8')
            try:
                header = self.headers[i]
            except:
                print(entry, '===> ', i, '==== HEADPROB')
                continue
            entry = self.begQuoteRemover.sub('', entry)
            entry = self.endQuoteRemover.sub('', entry)
            if header == 'category':
                category = int(entry)
            elif header == 'type':
                qType = entry
            elif header == 'question':
                question = entry
            elif header == 'answer':
                defaultAnswerID = self._processDefaultAnswer(entry)
            elif header.startswith('a-'):
                self._processAnswerForMCUG(defaultAnswerID, header, entry)

        self.dictionaryEntries.append(question)
        newEntry['category'] = category
        newEntry['qType'] = qType
        newEntry['question'] = question
        newEntry['answerID'] = defaultAnswerID
        newEntry['qID'] = len(self.questions)
        print(newEntry)
        self.questions.append(newEntry)
        

    def processFile(self, inputfile):
        dupQuoteRemover = re.compile(r'""')
        csvfile = codecs.open(inputfile, 'r', 'utf-8')
        csvreader = csv.reader(csvfile, delimiter=str(','), quotechar=str('"'))

        for row in csvreader:
            columns = row
            if len(self.headers) == 0:
                for column in columns:
                    column = unicode(column, 'utf-8').lower()
                    self.headers.append(column)
            else:
                self._processSingleLine(columns)


    def saveData(self, out_dir, cleanHTML=False):
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



try:
    options, arguments = getopt.getopt(sys.argv[1:], 'i:o:h', ['input=', 'output='])
except getopt.GetoptError:
    print('Usage:')
    print('\tpython csv2train.py -i <inputfile> -o <outputdir> [-h]')
    print()
    print('\t-i <inputfile>         Input CSV-File with ; as separator')
    print('\t-o <outputdir>         Output directory where converted files should be saved')
    print('\t-h                     Clean HTML (default=NO)')
    sys.exit(2)

verbose = False
dump = False
outputdir = None
inputfile = None
cleanHTML = False
for opt, arg in options:
    if opt in ('-i', '--input'):
        inputfile = arg	
    elif opt in ('-o', '--output'):
        outputdir = arg
    elif opt in ('-h'):
        cleanHTML = True

print("============================ CSV Converter ==============================")
print("               v1.0b - Copyright (c) 2017 M-AILABS GmbH")
print("           Written by: Imdat Solak (imdat@m-ailabs.bayern)")
print("=========================================================================")

if inputfile == None or outputdir == None:
    print('Usage: csv2train.py -i <inputfile> -o <outputdir>')
    sys.exit(1)

processor = QAManager()
processor.processFile(inputfile)
processor.saveData(outputdir, cleanHTML)
