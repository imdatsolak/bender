# -*- coding: utf-8 -*-
import sys 
reload(sys)
sys.setdefaultencoding("utf-8")
import os
import types
import logging
import json
from core import utils
from modules.dataextractors.mldataextractor import MLDataExtractor
from generic_modules.NameDetector import GenericNameDetector


"""
Class PersonDetector as described at:

Copyright (c) 2019 Imdat Solak

Created: 2017-08-23 07:00 CET, ISO
         This is the module that identifies and extracts names in requests
         This version is language-specific as it uses many different techniques
         It extracts ANY NAMES identified in the text. It uses a list of 
         Names in the supported languages as well as GenericNameDetector using
         an NLP-Engine.

"""
class PersonDetector(MLDataExtractor):
    def __init__(self, moduleConfig, configDictionary):
        super(PersonDetector, self).__init__(moduleConfig, configDictionary)
        self.profile = {
                'name' : 'persondetector',
                'class' : 'data-extractor',
                'supported-languages' : ['de', 'en', 'tr'],
                'variables': ['personfirstname', 'personlastname', 'personfullname', 'persongender']
                }
        self.logger = logging.getLogger(os.path.basename(sys.argv[0]))
        self.module_config = moduleConfig
        self.language = self.module_config.get('language', 'en')
        self.use_names = int(self.module_config.get('use-names', 0))
        self.female_names = None
        self.male_names = None
        self.unisex_names = None
        self.last_names = None
        if self.use_names == 1:
            self.female_names = self.module_config.get('female-names-file', None)
            self.male_names = self.module_config.get('male-names-file', None)
            self.unisex_names = self.module_config.get('unisex-names-file', None)
            self.last_names = self.module_config.get('last-names-file', None)

    def initForBender(self, benderInstance):
        self.benderCore = benderInstance
        nlp = self.benderCore.nlpModule()
        self.name_detector = GenericNameDetector(nlp, self.female_names, self.male_names, self.unisex_names, self.last_names)

    def extractDataFromRequest(self, request, originalRequest, sessionID):
        """
        The originalRequest is the request at it was written sent by the end user
        The "request" is the one already enriched with Concepts
        Returns the request with extracted data.
        For example:
            Request = 'Who was Steve Jobs'
            Returns = 'Who was <<PersonProperNameFull>>'

            Request = 'What is the weather in Munich for next week'
            Returns = 'What is the weather in <<LocationProperName>> for <<DateTime>>'

            Request = 'I had vacation last week, forgot to book it. What should I do?'
            Returns = 'I had vacation <<DateTime>>, forgot to book it. What should I do?'
        """
        foundEntries = self.name_detector.detectNamesInText(originalRequest)
        s = json.dumps(foundEntries)
        self.logger.info('PERSONDETECTOR: found results = {}'.format(s))
        if foundEntries is not None:
            sessionModule = self.benderCore.sessionModule()
            extractedDataSoFar = sessionModule.getExtractedDataForDataExtractor(self.profile['uid'], sessionID)
            if extractedDataSoFar == None:
                extractedDataSoFar = {}

            for entry in foundEntries:
                data = entry['text']
                key_type = entry['type']
                key_name = None
                if key_type == GenericNameDetector.FULLNAME:
                    key_name = 'personfullname'
                elif key_type == GenericNameDetector.LASTNAME:
                    key_name = 'personfirstname'
                elif key_type == GenericNameDetector.FIRSTNAME:
                    key_name = 'personlastname'
                elif key_type == GenericNameDetector.GENERICNAME:
                    key_name = 'personfullname'

                if key_name is not None:
                    extractedDataSoFar[key_name] = data

            sessionModule.storeExtractedDataInSession(extractedDataSoFar, self.profile['uid'], sessionID)

    def getExtractedVariablesInSession(self, sessionID):
        # Returns the list of all variables that have been extracted within the session 'sessionID'
        extractedDataSoFar = self.benderCore.sessionModule().getExtractedDataForDataExtractor(self.profile['uid'], sessionID)
        if extractedDataSoFar != None:
            return extractedDataSoFar.keys()
        return None

    def getValueForVariableInSession(self, variable, sessionID):
        # Returns the value found using the variable-extraction during the session
        # Returns None if there was no value...
        extractedDataSoFar = self.benderCore.sessionModule().getExtractedDataForDataExtractor(self.profile['uid'], sessionID)
        if extractedDataSoFar is not None:
            return extractedDataSoFar.get(variable, None)
        return None


"""
Class UserNameExtractor as described at:

Copyright (c) 2019 Imdat Solak

Created: 2017-08-23 07:00 CET, ISO
         This is the module that identifies and extracts names in requests
         This version is language-specific as it uses many different techniques
         It extracts the name of the CURRENT USER with whom Bender communicates.
         We do some heuristics on this, such as searching for "My name is...", 
         "I'm <Name>", ... in the languages we support.
         The actual name recognition happens in the GenericNameDetector
         This class provides the variables: 'UserFirstname', 'UserLastname', 'UserFullname',
         'UserGender'. The last one is detected using the name type (i.e. whether it is
         a femaleName or maleNamen). BEWARE: There are also UniSex names and you should 
         not rely on the Gender to be correct... In the future we might use oether techniques
         to detect the Gender of the user...

"""
class UserNameExtractor(MLDataExtractor):
    def __init__(self, moduleConfig, configDictionary):
        super(UserNameExtractor, self).__init__(moduleConfig, configDictionary)
        self.profile = {
                'name' : 'username-extractor',
                'class' : 'data-extractor',
                'uid' : 'USERNAMEEXTRACTOR-201708-ISO-V1-DEADBEEFDECAFBAD19690313',
                'supported-languages' : ['de', 'en', 'tr'],
                'variables': ['userfirstname', 'userlastname', 'userfullname', 'usergender']
                }
        self.module_config = moduleConfig

    def initForBender(self, benderInstance):
        self.benderCore = benderInstance
    
    def extractDataFromRequest(self, request, originalRequest, sessionID):
        """
        The originalRequest is the request at it was written sent by the end user
        The "request" is the one already enriched with Concepts
        Returns the request with extracted data.
        For example:
            Request = 'Hi, my name is Steve Jobs'
            Returns = 'Hi, my name is <<userfullename>>'
        """
        sessionModule = self.benderCore.sessionModule()
        data = 'EXTRACTED-DATA'
        key = 'VARIABLE-NAME'
        extractedDataSoFar = sessionModule.getExtractedDataForDataExtractor(self.profile['uid'], sessionID)
        if extractedDataSoFar == None:
            extractedDataSoFar = {}

        extractedDataSoFar[key] = data
        sessionModule.storeExtractedDataInSession(extractedDataSoFar, self.profile['uid'], sessionID)

    def getExtractedVariablesInSession(self, sessionID):
        # Returns the list of all variables that have been extracted within the session 'sessionID'
        extractedDataSoFar = self.benderCore.sessionModule().getExtractedDataForDataExtractor(self.profile['uid'], sessionID)
        if extractedDataSoFar != None:
            return extractedDataSoFar.keys()
        return None

    def getValueForVariableInSession(self, variable, sessionID):
        # Returns the value found using the variable-extraction during the session
        # Returns None if there was no value...
        extractedDataSoFar = self.benderCore.sessionModule().getExtractedDataForDataExtractor(self.profile['uid'], sessionID)
        if extractedDataSoFar != None:
            return extractedDataSoFar.get(variable, None)
        return None
