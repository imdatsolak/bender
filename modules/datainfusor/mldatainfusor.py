# -*- coding: utf-8 -*-
from __future__ import print_function
import sys 
reload(sys)
sys.setdefaultencoding("utf-8")
import re
import logging
import os

from modules.mlbendermodule import MLBenderModule
from modules.session.mlsession import MLSession

"""
Class MLDataInfusor as described at:
    https://wiki.ml.de/pages/viewpage.action?pageId=7145048

Copyright (c) 2019 Imdat Solak
                All Rights Reserved

"""
variable_detector = re.compile(r'{{[A-z]+}}')
class MLDataInfusor(MLBenderModule):
    def __init__(self, configDictionary):
        self.profile = {
                "name" : "mldata-infusor",
                "class" : "data-infusor",
                "supported-languages" : ["de"]
                }
        self.dataExtractors = None
        self.dataProviders = None
        self.dEIndexed = {}
        self.dPIndexed = {}
        self.logger = logging.getLogger(os.path.basename(sys.argv[0]))

    def initForBender(self, benderInstance):
        self.benderCore = benderInstance
    
    def setDataExtractorsAndProviders(self, dataExtractors, dataProviders):
        self.dataExtractors = dataExtractors
        self.dataProviders = dataProviders
        # Now, for performance reasons, remember what kind of variables each provide
        #
        # 1. For Data Extractors: In this case, the variable is just a unique name and should be the
        #    same as 'REQUIRED' by any DataProvider
        for dE in self.dataExtractors:
            variables = dE.getExtractableVariables()
            if variables != None:
                for variable in variables:
                    self.dEIndexed[variable] = dE

        # 2. For Data Providers: In this case, the data-providers may require various data from a 
        #    data extractor. This is defined in 'requiredVariables'
        for dP in self.dataProviders:
            variables = dP.getProvidedVariables()
            # here, variables is an array of dicts:
            #     [
            #        { 
            #          'name': <var-name>,
            #          'required': [<required-vars-from-data-extractor or session>]
            #        }, ...
            #     ]
            if variables != None:
                for key in variables.keys():
                    variableSpec = variables[key]
                    self.dPIndexed[key] = { 'dp':dP, 'required': variableSpec['required']}

    def _getDataExtractorsForRequiredVariables(self, requiredVars):
        dEs = []
        for rVar in requiredVars:
            dE = self.dEIndexed.get(rVar, None)
            if dE == None:
                print('*** Could not find DE for var %s ' % rVar)
            else:
                dEs.append(dE)
        if len(dEs):
            return dEs
        else:
            return None

    def _infuseDataToResponse(self, response, locationDataList):
        # We need to start replacing from the end, otherwise our indices will be screwed up
        returnResponse = response
        for l in sorted(locationDataList, key=lambda item: -item['begin']):
            replB = l['begin']
            replE = l['end']
            data = l['data']
            returnResponse = returnResponse[:replB] + data + returnResponse[replE:]

        return returnResponse

    def infuseDataToResponse(self, response, extractors, providers, sessionID, request, originalRequest, authoritative=True):
        """
        Returns updated response if successful
        Returns original response otherwise
        The variables in the response are identified with:
        {{_var-name_}}

        The variable names can only contain characters from [a-z] and [A-Z]. They can be CamelCase, e.g.:
            - {{userName}}
            - {{currentDate}}
            - {{currentTime}}
        TODO: use the correct extraction with the CURRENT SESSION otherwise we may
              use data extracted from other user's sessions :-)))
              ACTUALLY: The whole session-specific data extraction/provision needs to be
              integrated, currently there is NONE!!!!
        """
        sessionModule = self.benderCore.sessionModule()
        iterator = variable_detector.finditer(response)
        locationsAndData = []
        if iterator != None:
            for match in iterator:
                matchS = match.span()[0]
                matchE = match.span()[1]
                matchedText = response[matchS:matchE]
                if matchedText:
                    matchedText = matchedText.replace('{{', '') 
                    matchedText = matchedText.replace('}}', '')
                    foundVariable = matchedText
                    missingExtractedData = False
                    if foundVariable in self.dPIndexed.keys():
                        dPData = self.dPIndexed[foundVariable]
                        dataProvider = dPData['dp']
                        requiredVars = dPData['required']
                        if requiredVars is not None and len(requiredVars) > 0:
                            requiredDEs = self._getDataExtractorsForRequiredVariables(requiredVars)
                            if requiredDEs == None:
                                print('*** ERROR: Could not find any data extractors for my data provider')
                                return response, authoritative
                        else:
                            requiredDEs = None

                        newData, missingExtractedData = dataProvider.provideDataForVariable(foundVariable, requiredDEs, sessionID)
                        if newData != None:
                            locationsAndData.append({'begin': matchS, 'end': matchE, 'data': newData})
                        elif missingExtractedData:
                            self.logger.info('Missing pre-condition data..')

        if len(locationsAndData):
            return self._infuseDataToResponse(response, locationsAndData), authoritative
        else:
            return response, authoritative

