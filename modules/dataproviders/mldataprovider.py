# -*- coding: utf-8 -*-
import sys 
reload(sys)
sys.setdefaultencoding("utf-8")
import logging
import os

from modules.mlbendermodule import MLBenderModule
"""
Class MLDataProvider as described at:
    https://wiki.ml.de/pages/viewpage.action?pageId=7144585

Copyright (c) 2019 Imdat Solak
                All Rights Reserved
"""
class MLDataProvider(MLBenderModule):
    def __init__(self, moduleConfig, configDictionary):
        super(MLDataProvider, self).__init__(configDictionary)
        self.profile = {
                "name" : "mldata-provider",
                "class" : "data-provider",
                "supported-languages" : [],
                }
        self.logger = logging.getLogger(os.path.basename(sys.argv[0]))
        self.module_config = moduleConfig
        self.variables = {
                'benderversion': {
                    'required': [],
                    'optional': [],
                    'processor': self._getVersion,
                    'na-processor': self._cannot
                    }
                }

    def initForBender(self, benderInstance):
        self.benderCore = benderInstance

    def getProvidedVariables(self):
        return self.variables 

    def _getVersion(self, variable, extractedValues):
        return '1.1.0b'

    def _cannot(self, variable):
        return ''

    def canProvideDataForVariable(self, variable, dataExtractors, sessionID):
        varReqData = []
        if variable in self.variables.keys():
            varSpec = self.variables[variable]
            varRequirements = varSpec['required']
            for requiredVariable in varRequirements:
                for extractor in dataExtractors:
                    # TODO: We should not look into the extractor's internal data
                    # structure but instead have a method for it...
                    if extractor.canExtractVariable(requiredVariable):
                        varReqData.append({'requiredVariable' : requiredVariable, 'extractor': extractor})
                        break

        self.logger.info('Var Req Data Len {:d}, varRs {:d}'.format(len(varReqData), len(varRequirements)))
        if len(varReqData) < len(varRequirements):
            return False, None
        else:
            return True, varReqData

    def cannotProvideDataMessageForVariable(self, variable, dataExtractors, sessionID):
        func = self.variables[variable].get('na-processor',None)
        if func is not None:
            return func(variable, extractedValues)
        else:
            return None

    def provideDataForVariable(self, variable, dataExtractors, sessionID):
        canProvideData, dataExtractorSpecs = self.canProvideDataForVariable(variable, dataExtractors, sessionID)
        if canProvideData:
            extractedValues = {}
            if dataExtractors is not None and len(dataExtractors) > 0:
                for deSpec in dataExtractorSpecs:
                    rVar = deSpec['requiredVariable']
                    dE = deSpec['extractor']
                    value = dE.getValueForVariableInSession(rVar, sessionID)
                    extractedValues[rVar] = value

            retval =  self.variables[variable]['processor'](variable, extractedValues)
            self.logger.info('Response is {}'.format(retval))
            return retval, False

        return None, True

