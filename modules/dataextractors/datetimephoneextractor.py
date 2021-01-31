# -*- coding: utf-8 -*-
from __future__ import print_function
import sys 
reload(sys)
sys.setdefaultencoding("utf-8")
import os
import re
import codecs
from generic_modules.DTPDetector import MLDateTimePhoneDetector
from modules.dataextractors.mldataextractor import MLDataExtractor

class MLDateTimePhoneExtractor(MLDataExtractor):
    def __init__(self, moduleConfig, configDictionary):
        super(MLDateTimePhoneExtractor, self).__init__(moduleConfig, configDictionary)
        self.profile = {
                    'name': 'mldatatimephone-extractor',
                    'class': 'data-extractor',
                    'supported-languages': ['de', 'en', 'tr']
                }
        self.module_config = moduleConfig
        self.data_detector = MLDateTimePhoneDetector()

    def extractDataFromRequest(self, request, originalRequest, sessionID):
        detectedItems = self.data_detector.detectDataInText(request)
        if detectedItems != None:
            self.benderCore.sessionModule().storeExtractedDataInSession(detectedItems, self.profile['uid'], sessionID)
        else:
            self.benderCore.sessionModule().deleteExtractedDataInSession(self.profile['uid'], sessionID)

    def getExtractedVariablesInSession(self, sessionID):
        retArr = None
        extractedItems = self.benderCore.sessionModule().getExtractedDataForExtractor(self.profile['uid'], sessionID)
        if extractedItems != None:
            retArr = []
            for entry in extractedItems:
                retArr.append(entry['type'])
        return retArr

    def getValueForVariableInSession(self, variable, sessionID):
        extractedItems = self.benderCore.sessionModule().getExtractedDataForExtractor(self.profile['uid'], sessionID)
        if extractedItems != None:
            for entry in extractedItems:
                if entry['type'] == variable:
                    return entry['found']
        return None

