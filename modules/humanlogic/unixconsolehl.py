# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import sys 
reload(sys)
sys.setdefaultencoding("utf-8")

import readline
from modules.humanlogic.mlhumanlogic import MLHumanLogic
"""
Class UnixConsoleHumanLogic as described at:

Copyright (c) 2019 Imdat Solak
                All Rights Reserved
"""
class UnixConsoleHumanLogic(MLHumanLogic):
    def __init__(self, configDictionary):
        super(UnixConsoleHumanLogic, self).__init__(configDictionary)
        self.profile = {
                "name" : "unixconsole-human-logic",
                "class" : "human-logic",
                "supported-languages" : ["de_DE", "en_US"],
                "isAsync" : False
                }
        print("*******************************************************************")
        print("************ Bender UnixConsole Human Logic Interface. *************")
        print("*******************************************************************")

    def initForBender(self, benderInstance):
        self.benderCore = benderInstance

    def capabilities(self):
        return self.profile
    
    def makeResponse(self, responseString, originalResponse=None, machineResponseWasSelected=False):
        if originalResponse:
            theResponse = originalResponse
            theResponse['original-logicengine-name'] = originalResponse['logicengine-name']
            theResponse['original-logicengine-class'] = originalResponse['logicengine-class']
        else:
            theResponse = {}
        theResponse['response'] = responseString
        theResponse['confidenceLevel'] = 1.0
        if machineResponseWasSelected:
            theResponse['machineResponseSelected'] = True
        return theResponse

    def processRequestWOCalcResponses(self, originalRequest, enrichedRequest):
        returnResponse = ''
        print('\a')
        print("        -----------------USER-REQUEST---------------------")
        print("ORIGINAL=> ", originalRequest)
        print("ENRICHED=> ", enrichedRequest)
        print("        ---------------NO CALCULATED RESPONSE----------------")
        print("        ------------------YOUR RESPONSE-------------------")
        yn = "n"
        while yn == "n":
            returnResponse = raw_input("> ")
            yn = raw_input("Correct ([Y]es, [N]o, [A]bort? ")
            if yn.lower() == 'y':
                print("\nThank you...")
                print("        -----------------------EOT------------------------\n")
                return self.makeResponse(returnResponse, None)
            elif yn.lower() == 'a':
                print('Returning <none>')
                print("        -----------------------EOT------------------------\n")
                return None
        return None

    def _retrieveResponseText(self, response):
        responseActualText = response['response']
        try:
            responseIsID = response['responseIsID']
        except:
            responseIsID = False

        if responseIsID:
            idxResponseProc = self.benderCore.indexedResponseProcessorModule()
            responseID = response['response']
            try:
                rID = int(responseID)
                responseActualText, responseType = idxResponseProc.getIndexedReponseContent(rID)
                if not responseActualText:
                    responseActualText = response['response']
            except:
                responseActualText = response['response']

        return responseActualText 

    def _getBetterRatedResponse(self, aResponse, allResponses):
        returnResponse = aResponse
        for response in allResponses:
            if (response['response'] == aResponse['response']) and (float(response['confidenceLevel']) > float(aResponse['confidenceLevel'])):
                returnResponse = response
        return returnResponse


    def _removeDuplicateEntriesFromResponses(self, rawResponses):
        cleanedResponses = []
        for response in rawResponses:
            betterResponse = self._getBetterRatedResponse(response, rawResponses)
            cleanedResponses.append(betterResponse)
        return cleanedResponses

    def processRequestWithCalcResponses(self, fullRequestData, calculatedResponses):
        # TODO:
        #      Fix this original/enriched-stuff
        originalRquest = fullRequestData['originalRequest']
        enrichedRequest = originalRequest
        rawResponses = calculatedResponses
        rawResponses = sorted(calculatedResponses, key=lambda item: float(item['confidenceLevel']), reverse=True)
        calculateResponses = []
        # Now remove duplicate responses
        for response in rawResponses:
            skipThisOne = False
            for r in calculatedResponses:
                if response['response'] == r['response']:
                    skipThisOne = True
                    break
            if not skipThisOne:
                calculatedResponses.append(response)

        calculatedResponses = calculatedResponses[:10]

        print('\a')
        print("        -----------------USER-REQUEST---------------------")
        print("ORIGINAL=> ", originalRequest)
        print("ENRICHED=> ", enrichedRequest)
        print("        --------------CALCULATED RESPONSE(s)--------------")
        maxResponse = len(calculatedResponses)
        for i in xrange(len(calculatedResponses)):
            calcResp = calculatedResponses[i]
            print('[%02d] (CL: %2.1f%%) %s' % (i+1, float(calcResp['confidenceLevel'])*100.0, self._retrieveResponseText(calcResp)))
            print('- ' * 40)
        print('')
        print('{N}ew Response')
        print('{A}bort')
        print("        ------------------YOUR RESPONSE-------------------")
        originalResponse = None
        selection = 'z'
        machineResponseWasSelected = False
        while selection == 'z':
            selection = raw_input('SELECTION [1.., N, A] >')
            if selection.isdigit() and int(selection) <= maxResponse and int(selection) > 0:
                originalResponse = calculatedResponses[int(selection)-1]
                returnResponse = originalResponse['response']
                machineResponseWasSelected = True
                print("\nThank you...")
                print("        -----------------------EOT------------------------\n")
            elif selection.lower() == 'n':
                yn = "n"
                while yn == "n":
                    returnResponse = raw_input("YOUR RESPONSE> ")
                    yn = raw_input("Correct ([Y]es, [N]o, [A]bort? ")
                    if yn.lower() == 'y':
                        print("\nThank you...")
                        print("        -----------------------EOT------------------------\n")
                        originalResponse = None
            elif selection.lower() == 'a':
                print("\tReturning <none>")
                print("        -----------------------EOT------------------------\n")
                originalResponse = None
                return None
            else:
                selection = 'z'
        return self.makeResponse(returnResponse, originalResponse, machineResponseWasSelected)

    def processRequest(self, originalRequest, enrichedRequest, calculatedResponses=None):
        if calculatedResponses and len(calculatedResponses)>0:
            return self.processRequestWithCalcResponses(originalRequest, enrichedRequest, calculatedResponses)
        else:
            return self.processRequestWOCalcResponses(originalRequest, enrichedRequest)
  
    def jobStatus(self, jobID):
        return None
  
    def deleteJob(self, jobID):
        return True
  
    def getResponseForJobID(self, jobID):
        return None
