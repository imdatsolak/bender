# -*- coding: utf-8 -*-
import sys 
reload(sys)
sys.setdefaultencoding("utf-8")

from modules.mlbendermodule import MLBenderModule
"""
Class MLDataExtractor as described at:

Copyright (c) 2019 Imdat Solak
                All Rights Reserved

"""
class MLDataExtractor(MLBenderModule):
    def __init__(self, moduleConfig, configDictionary):
        super(MLDataExtractor, self).__init__(configDictionary)
        self.profile = {
                "name" : "mldata-extractor",
                "class" : "data-extractor",
                "supported-languages" : ["de"],
                'variables' : ['version']
                }
        self.module_config = moduleConfig
        self.variables = None


    def initForbender(self, benderInstance):
        self.benderCore = benderInstance

    
    def getExtractableVariables(self):
        if self.variables is None:
            self.variables =  self.profile.get('variables', None)
        if self.variables is not None:
            return self.variables
        return None


    def canExtractVariable(self, variable):
        ev = self.getExtractableVariables()
        if ev is not None and variable in ev:
            return True
        return False


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
