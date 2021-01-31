# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import sys 
reload(sys)
sys.setdefaultencoding("utf-8")

import readline
from core import utils
import json
import os
import logging
from time import sleep
from modules.mlbendermodule import MLBenderModule
"""
Copyright (c) 2019 Imdat Solak
                All Rights Reserved
"""
class MLHumanLogic(MLBenderModule):
    def __init__(self, configDictionary):
        super(MLHumanLogic, self).__init__(configDictionary)
        self.profile = {
                "name" : "ml-human-logic",
                "class" : "human-logic",
                "supported-languages" : ["de_DE", "en_US"],
                "isAsync" : False
                }
        self.storage = None
        self.jobID = None
        self.logger = logging.getLogger(os.path.basename(sys.argv[0]))

    def initForBender(self, benderInstance):
        self.benderCore = benderInstance
        self.storage = benderInstance.transientStorageModule()
        # print('   | *** HLI-Interface = WebUI @ http://<benderserver>/ui/hli ...')

    def capabilities(self):
        return self.profile

    def _makeResponse(self, response):
        theResponse = {}
        theResponse.update(response)
        self.logger.info('HLI::WEB::RESPONSE = %s ' % json.dumps(response))

        theResponse['original-logicengine-name'] = theResponse.get('logicengine-name', None)
        theResponse['original-logicengine-class'] = theResponse.get('logicengine-class', None)
        theResponse['response'] = theResponse['responseText']
        theResponse['confidenceLevel'] = 1.0
        if theResponse['responseWasSelected']:
            theResponse['machineResponseSelected'] = True
        return theResponse

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

        return responseActualText, responseIsID 

    def processRequest(self, fullRequestData, calculatedResponses=None, jobID=None, sessionID=None):
        self.jobID = utils.getUniqueID(insertAtEnd=999)
        self.benderJobID = jobID
        self.sessionID = sessionID
        foundResponseTexts = []
        if calculatedResponses and len(calculatedResponses)>0:
            rawResponses = calculatedResponses
            rawResponses = sorted(calculatedResponses, key=lambda item: float(item['confidenceLevel']), reverse=True)
            storedCalcResponses = {}
            # Now remove duplicate responses
            respCount = 0
            for response in rawResponses:
                skipThisOne = False
                if response['response'] in storedCalcResponses.keys():
                    skipThisOne = True
                if not skipThisOne:
                    respCount += 1
                    responseText, responseIsID = self._retrieveResponseText(response)
                    if responseText not in foundResponseTexts:
                        thisResponse = {}
                        thisResponse.update(response)
                        thisResponse['responseText'] = responseText
                        thisResponse['qID'] = response['response']
                        if response.get('qType', None) == None:
                            thisResponse['qType'] = 'e'
                        storedCalcResponses[response['response']] = thisResponse
                        foundResponseTexts.append(responseText)
                    
                if respCount == 10:
                    break

            data = {
                    'calculatedResponses': storedCalcResponses,
                    'status': 'WiP' # one of "WiP", "LOCKED", "DONE"
                    }
        else:
            data = {
                    'status': 'WiP' # one of "WiP", "LOCKED", "DONE"
                    }

        data.update(fullRequestData)
        dataAsString = json.dumps(data)
        self.storage.storeDataForKey(data=dataAsString, key=self.jobID, ownerID=self.profile['uid'])
        jobDone = False
        jobGone = False
        goneReason = -1
        agentNameOrID = '<UNKNOWN>'
        # We also need to add a timeout below...
        data = {}
        while jobDone == False and jobGone == False:
            dataAsString = self.storage.dataForKey(self.jobID, self.profile['uid'])
            if dataAsString:
                data = json.loads(dataAsString)
                if data['status'] == 'DELETED':
                    goneReason = data['reason']
                    agentNameOrID = data['agentNameOrID']
                    jobGone = True
                    self.storage.deleteDataForKey(key=self.jobID, ownerID=self.profile['uid'])
                elif data['status'] == 'DONE':
                    jobDone = True
                else:
                    sleep(0.200)
            else:
                jobGone = True

        if not jobGone:
            finalResponse = None
            response = data.get('response')
            if response != None:
                finalResponse = self._makeResponse(response)

            self.storage.deleteDataForKey(key=self.jobID, ownerID=self.profile['uid'])
            self.logger.info('HLI::WEBUI returning %s' % json.dumps(finalResponse))
            return finalResponse
        else:
            self.logger.info('HLI::WEBUI Request {} was deleted by {} for reason {}'.format(self.jobID, agentNameOrID, goneReason))

        return None

    def getListOfJobs(self, agentNameOrID=''):
        allData = self.storage.allDataForOwner(self.profile['uid'])
        data = {}
        if allData:
            for key in allData.keys():
                dataAsDict = json.loads(allData[key])
                if dataAsDict['status'] != 'DONE' and dataAsDict['status'] != 'DELETED':
                    data[key] = dataAsDict
            return {'requests': data}, 200
        else:
            return {}, 200

    def lockJob(self, jobID, agentNameOrID=''):
        data = None
        dataAsString = self.storage.dataForKey(jobID, self.profile['uid'])
        if dataAsString:
            data = json.loads(dataAsString)
        if data != None and data['status'] == 'WiP':
            data['status'] = 'LOCKED'
            data['agentNameOrID'] = agentNameOrID
            dataAsString = json.dumps(data)
            self.storage.storeDataForKey(data=dataAsString, key=jobID, ownerID=self.profile['uid'])
            return 200
        return 404

    def deleteJob(self, jobID, reason=1, agentNameOrID=''):
        self.logger.info('INFO::WEBUI Request Deleted: %s ' % jobID)

        data = None
        dataAsString = self.storage.dataForKey(jobID, self.profile['uid'])
        if dataAsString:
            data = json.loads(dataAsString)
        if data != None:
            data['status'] = 'DELETED'
            data['reason'] = reason
            data['agentNameOrID'] = agentNameOrID
            dataAsString = json.dumps(data)
            self.storage.storeDataForKey(data=dataAsString, key=jobID, ownerID=self.profile['uid'])
            return 200
        return 404

    def unlockJob(self, jobID, agentNameOrID=''):
        data = None
        dataAsString = self.storage.dataForKey(jobID, self.profile['uid'])
        if dataAsString:
            data = json.loads(dataAsString)
        if data != None and data['status'] == 'LOCKED':
            data['status'] = 'WiP'
            data['agentNameOrID'] = agentNameOrID
            dataAsString = json.dumps(data)
            self.storage.storeDataForKey(data=dataAsString, key=jobID, ownerID=self.profile['uid'])
            return 200
        return 404

    def answerJob(self, responseData):
        jobID = responseData['requestID']
        data = None
        dataAsString = self.storage.dataForKey(jobID, self.profile['uid'])
        if dataAsString:
            data = json.loads(dataAsString)
        if data != None: # and data['status'] == 'LOCKED':
            data['status'] = 'DONE'
            data['response'] = responseData['response']
            data['agentNameOrID'] = responseData.get('agentNameOrID', '1')
            dataAsString = json.dumps(data)
            self.storage.storeDataForKey(data=dataAsString, key=jobID, ownerID=self.profile['uid'])
            return 200
        return 404

