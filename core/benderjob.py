# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

import threading
import time
import datetime
import json
import logging
import os
import json
import hashlib
import codecs
from core import utils
from gensim import corpora
from modules.machinelogic.mlmachinelogic import MLMachineLogic
from modules.requestproc.mlreqproc import MLRequestProcessor
"""
Class BenderJob
This class performs the MULTI-THREADED work. Each instance represents a unique request Job
This runs as long as there is still a machine-logic that hasn't responded OR until the job-timeout
is reached.

It is used internall by BenderCore only

Copyright (c) 2019 Imdat Solak
                 All Rights Reserved

Created: 2016-04-19 10:00 CET, ISO
"""
def learn_or_retrain(benderJob, qToLearn, aToLearn, qType, qCategory, mcugAnswers, reinforce, benderCore):
    newQAPair = (qToLearn, aToLearn)
    questionIndexed, answerIndexed = benderCore.getBrain().addNewQAPair(newQAPair, qType, qCategory, mcugAnswers)
    benderCore.similarityModule().addNewQAPair(questionIndexed, answerIndexed)
    benderCore.addNewQAPairToMachines(questionIndexed, answerIndexed)


def _learnNewQAPair(question, answer):
    """
    What do we need to do here?
    1) Add the new Q/A-Pair to MLBrain
    2) Add the new Q/A-Pair to Similarity-Engine
    3) Prepare new data for Neuronal Networks
    """
    return True


def _reinforceQAPair(question, answer):
    """
    Similar to above, we need to tell the system that the answer above was, in fact, the actually
    correct answer for the question. For this, we need to somehow store this information in the Brain
    as well as in the Similarity-Engine. This is no problem.
    But... we also have to tell the Neuronal Networks that they should re-inforce their learning.
    How do we do this???
    """
    return True


class BenderJobLogger(object):
    rgBENDER = 'BENDER'
    rgAGENT = 'HLI'
    rgDELETED = 'DELETED'
    def __init__(self, configDictionary):
        self.config = configDictionary
        self.key = 'nmxcvjkhsdf98u53429kjhasd901423jkhdsfzcxvmnuitgre4325809cneu3io'
        log_path = utils.getKeyFromSectionInConfiguration('bender-core', 'log_directory', 'logs', configDictionary)
        hash_key = utils.getKeyFromSectionInConfiguration('bender-core', 'log_hash', None, configDictionary)
        self.lock = threading.Lock()
        if hash_key == None:
            logger = logging.getLogger(os.path.basename(sys.argv[0]))
            logger.error('Missing `log_hash` in `bender-core` section of configuration file. Will exit!')
            sys.exit(1)
        new_hash_key = self.key + hash_key
        self.hash_key = hashlib.sha256(new_hash_key).hexdigest()
        requests_log_file = os.path.join(log_path, 'requests.log')
        if os.path.exists(requests_log_file):
            allentries = codecs.open(requests_log_file, 'r', 'utf-8').readlines()
            if len(allentries) > 0:
                self.last_req_log_entry = allentries[-1].strip()
            else:
                self.last_req_log_entry = None
        else:
            self.last_req_log_entry = None
        self.requests_log_file = codecs.open(requests_log_file, 'a', 'utf-8')
        p_log_file = os.path.join(log_path, 'performance.log') 
        if os.path.exists(p_log_file):
            allentries = codecs.open(p_log_file, 'r', 'utf-8').readlines()
            if len(allentries) > 0:
                self.last_log_entry = allentries[-1].strip()
            else:
                self.last_log_entry = None
        else:
            self.last_log_entry = None
        self.performance_log_file = codecs.open(p_log_file, 'a', 'utf-8')

    def log_request(self, original_request, request_found, response, hcl, lcl, acl, logicE, found_by, other_params):
        # NOTE: We are using md5 for hashing. I know that md5 has collision issues
        #       but it is significantly faster than SHA256 and we don't care about
        #       collision here. We just want to know whether the line was temepered
        #       with or not. For that, md5 is enough and we don't waste CPU-cyles 
        #       for this task as this logging will happen very, very often...
        #       Imdat Solak (iso), 2017-07-21 10:30 CET
        self.lock.acquire()
        if response == None:
            response = 'NONE'
        if other_params == None:
            other_params = 'NONE'
        if logicE == None:
            logicE = 'NONE'
        if request_found == None:
            request_found = 'NONE'
        log_time_seconds = time.time()
        log_time = time.localtime(log_time_seconds)
        log_time_string = time.asctime(log_time)
        oroginal_request = original_request.replace('\n', '')
        request_found = request_found.replace('\n', '')
        requests_log_entry = '\t'.join([str(log_time_seconds), log_time_string, original_request, request_found, response, str(acl), str(lcl), str(hcl), logicE, found_by, other_params])
        if self.last_req_log_entry is not None:
            requests_last_hash = self.last_req_log_entry.split('\t')[-1]
        else:
            requests_last_hash = self.hash_key
        request_hash = hashlib.md5(requests_log_entry + requests_last_hash).hexdigest()
        print(requests_log_entry, request_hash, sep='\t', file=self.requests_log_file)
        self.requests_log_file.flush()
        self.last_req_log_entry = requests_log_entry + '\t' + request_hash
        # When the response was found by Bender itself (automatically generated) then
        # we log it also in the performance log-file. This is a counter-part to the 
        # request log-file, but it only contains a subset...
        if found_by == self.rgBENDER:
            perf_log_entry = '\t'.join([str(log_time_seconds), log_time_string, str(acl), str(lcl), str(hcl), request_hash])
            if self.last_log_entry != None:
                prev_log_hash = self.last_log_entry.split('\t')[-1]
            else:
                prev_log_hash = self.hash_key
            new_hash = hashlib.md5(perf_log_entry + prev_log_hash + self.hash_key).hexdigest()
            perf_log_entry = '\t'.join([perf_log_entry, new_hash])
            self.last_log_entry = perf_log_entry
            print(perf_log_entry, file=self.performance_log_file)
            self.performance_log_file.flush()
        self.lock.release()


class BenderJob(threading.Thread):
    jobStatusWIP = 202
    jobStatusDONE = 200
    jobStatusFORWARDED = 307
    jobStatusREJECTED = 422
    jobStatusKILLED = 404
    currentJobNo = 0
    REJECT_REQUEST = 100
    AUTOFORWARD_REQUEST = 200
    PROCESS_REQUEST = 1000
    def __init__(self, threadID, benderInstance, useSimilarity = True, jobLogger = None, use_hli=1, interactive=0, num_results=1, use_lookup=1):
        threading.Thread.__init__(self)
        self.logger = logging.getLogger(os.path.basename(sys.argv[0]))
        self.threadID = threadID
        self.jobID = ""
        self.benderCore = benderInstance
        self.hcl = self.benderCore.higherConfidenceLevel()
        self.lcl = self.benderCore.lowerConfidenceLevel()
        self.use_hli = use_hli
        self.interactive = interactive
        self.num_results = num_results
        self.responseArray = []
        self.useSimilarity = useSimilarity
        self.machineLogicModule = self.benderCore.newMachineLogic()
        self.internalMachineLogics = self.benderCore.internalMachineLogicModules()
        self.indexedResponseProcessor = self.benderCore.indexedResponseProcessorModule()
        self.permanentStorage = self.benderCore.storageModule()
        self.use_lookup = use_lookup
        self.lookup = self.benderCore.lookupModule()
        self.dataProviders = self.benderCore.dataProviderModules()
        self.dataExtractors = self.benderCore.dataExtractorModules()
        self.dataInfusor = self.benderCore.dataInfusorModule()
        self.responsePostProcessor = self.benderCore.responseProcessorModule()
        self.sessionModule = self.benderCore.sessionModule()
        self.preprocessingModules = self.benderCore.preprocessingModules()
        self.conceptModule = self.benderCore.conceptModule()
        self.spellingModule = self.benderCore.spellingModule()
        self.brain = self.benderCore.getBrain()
        self.finalResponse = None
        self.fullRequestData = None
        self.needsLearning = False
        self.qToLearn = ''
        self.aToLearn = ''
        self.qType = 'e'
        self.qCategory = 1
        self.mcugAnswers = []
        self.reinforce = False
        self.job_logger = jobLogger
        self.taskToPerform = self.PROCESS_REQUEST
        # We usually have eight(!, excl. lemmatized versions) variants of a request coming in:
        #   - Original Request
        #   - Spell Checked Request
        #   - Enriched Request
        #   - Enriched Spell Checked Rquest
        #   - Conceptualized (original) Request
        #   - Conceptualized spell-checked request
        #   - Conceptualized, Enriched Request
        #   - Conceptualized, enriched, spell-checked request
        #   - Lemmatized: TBD
        #
        # Thus, we need to check for all eight of them every time. The reason why this is not built
        # into the machines directly is that otherwise we would lose the information which request
        # we used to find something (in case, we *do* find something :-)
        self.requestKeys = {
                '1-originalRequest': ['responseIsForOriginalRequest', 'originalRequestWas', 'originalRequest'],
                '2-spellCheckedRequest': ['responseIsForSpellCheckedQuery', 'spellCheckedQueryWas', 'spellCheckedRequest'],
                '3-enrichedOriginalRequest': ['responseIsForEnrichedQuery', 'enrichedQueryWas', 'enrichedOriginalRequest'],
                '4-enrichedSpellCheckedRequest': ['responseIsForEnrichedSpellCheckedQuery', 'enrichedSpellCheckedQueryWas', 'enrichedSpellCheckedRequest'],
                '5-conceptualizedOriginalRequest': ['responseIsForConceptualizedQuery', 'conceptualizedQueryWas', 'conceptualizedOriginalRequest'],
                '6-conceptualizedSpellCheckedRequest': ['responseIsForConceptualizedSpellCheckedQuery', 'conceptualizedSpellCheckedQueryWas', 'conceptualizedSpellCheckedRequest'],
                '7-conceptualizedEnrichedOriginalRequest': ['responseIsForConceptualizedEnrichedQuery', 'conceptualizedEnrichedQueryWas', 'conceptualizedEnrichedOriginalRequest'],
                '8-conceptualizedEnrichedSpellCheckedRequest': ['responseIsForConceptualizedEnrichedSpellCheckedQuery', 'conceptualizedEnrichedSpellCheckedQueryWas', 'conceptualizedEnrichedSpellCheckedRequest']
                }

    def _checkSyncMachines(self, methodToCall):
        foundResponses = []
        foundSomething = False
        checkedRequests = []
        for requestKey in sorted(self.requestKeys.keys()):
            # Let's see if this request-type is identical to one of the previous (e.g. spell-checked version == original version)
            # in such a case, we don't need to ask our (expensive) machines again
            request = self.fullRequestData[self.requestKeys[requestKey][2]]
            if len(request)>0 and request not in checkedRequests:
                responseFound, responses = methodToCall(request)
                if responseFound:
                    foundSomething = True
                    for response in responses:
                        response[self.requestKeys[requestKey][0]] = 1
                        response[self.requestKeys[requestKey][1]] = request
                        containsDefinitiveAnswer = False
                        response['qType'] = 'm'
                        response['category'] = 1
                        if response.get('responseIsID', False) == True:
                            rID = int(response['response'])
                            iResponses = self.indexedResponseProcessor.getIndexedResponses(rID)
                            # Let's see if contains a definitive answer (authoritative) and save that as well
                            # as the category of the question
                            if iResponses:
                                for singleResponse in iResponses:
                                    response['category'] = singleResponse.get('category', 1)
                                    if singleResponse.get('qType', 'e').lower() == 'e':
                                        response['qType'] = 'e'
                                        break
                        foundResponses.append(response)
                    if self.haveResponseAboveConfidenceLevel(responses, self.hcl):
                        break
                checkedRequests.append(request)
        return foundSomething, foundResponses

    def _checkLookupCacheForRequest(self, request):
        # Let's first ask our lookup-engine if it has something matching
        responseFound = False
        responseArray = None
        lookup = self.benderCore.lookupModule()
        response = lookup.lookupRequest(request)
        if response:
            responseFound = True
            responseArray = []
            responseDict = json.loads(response)
            # Since this one is coming from the lookup-engine, we should add it to the name
            # But we should preserve the original machine logic in case we need it in the future
            responseDict['original-logicengine-name'] = responseDict['logicengine-name']
            responseDict['original-logicengine-class'] = responseDict['logicengine-class']
            responseDict['logicengine-name'] = lookup.getModuleName()
            responseDict['logicengine-class'] = lookup.getModuleClass()
            responseArray.append(responseDict)
        return responseFound, responseArray

    def _checkLookupCache(self):
        return self._checkSyncMachines(self._checkLookupCacheForRequest)

    def _checkInternalSimilarityForRequest(self, request):
        responseFound = False
        responseArray = None
        simModule = self.benderCore.similarityModule()
        sims = simModule.getSimilarEntriesFromCorpus(request)
        if sims:
            responseFound = True
            responseArray = []
            for sim in sims:
                responseDict = {}
                responseDict['logicengine-name'] = simModule.getModuleName()
                responseDict['logicengine-class'] = simModule.getModuleClass()
                responseDict['response'] =  str(sim[0])
                responseDict['confidenceLevel'] = str(sim[1])
                responseDict['responseIsID'] = 1
                responseArray.append(responseDict)
        return responseFound, responseArray

    def _checkInternalSimilarity(self):
        return self._checkSyncMachines(self._checkInternalSimilarityForRequest)

    def _checkInternalMachinesForRequest(self, request):
        responseFound = False
        responseArray = []
        for iML in self.internalMachineLogics:
            responses = iML.performTextQuery(request, num_results=self.num_results, jobID = self.jobID)
            if responses and len(responses):
                responseFound = True
                for response in responses:
                    responseDict = {}
                    responseDict['logicengine-name'] = iML.getModuleName()
                    responseDict['logicengine-class'] = iML.getModuleClass()
                    responseDict.update(response)
                    responseArray.append(responseDict)
        if len(responseArray):
            return responseFound, responseArray
        else:
            return False, None

    def _checkInternalMachines(self):
        # NOTE: This may change to async-call at one point
        #       For now, we leave it synchronously
        return self._checkSyncMachines(self._checkInternalMachinesForRequest)

    def _checkPrimaryExternalMachinesForRequest(self, request):
        responseArray = None
        responseFound = False
        machineResponses = self.machineLogicModule.performTextQuery(request, machinesToAsk = MLMachineLogic.askPrimaryMachines)
        if machineResponses and self.haveResponseAboveConfidenceLevel(machineResponses, self.lcl):
            responseArray = []
            responseFound = True
            responseArray.extend(machineResponses)
        return responseFound, responseArray

    def _checkPrimaryExternalMachines(self):
        # NOTE: This may change to async-call at one point
        #       For now, we leave it synchronously
        return self._checkSyncMachines(self._checkPrimaryExternalMachinesForRequest)

    def _checkSecondaryExternalMachinesForRequest(self, request):
        responseArray = None
        responseFound = False
        machineResponses = self.machineLogicModule.performTextQuery(request, machinesToAsk = MLMachineLogic.askSecondaryMachines)
        if machineResponses and self.haveResponseAboveConfidenceLevel(machineResponses, self.lcl):
            responseArray = []
            responseFound = True
            responseArray.extend(machineResponses)
        return responseFound, responseArray

    def _checkSecondaryExternalMachines(self):
        # NOTE: This may change to async-call at one point
        #       For now, we leave it synchronously
        return self._checkSyncMachines(self._checkSecondaryExternalMachinesForRequest)

    def _askHumanLogic(self, responsesSoFar):
        responseArray = None
        responseFound = False
        humanLogic = self.benderCore.newHumanLogicInstance()
        if len(responsesSoFar):
            responsesSoFar = sorted(responsesSoFar, key=lambda item: float(item['confidenceLevel']), reverse=True)
            humanLogicResponseDict = humanLogic.processRequest(self.fullRequestData, responsesSoFar, jobID=self.jobID, sessionID=self.uuid)
        else:
            humanLogicResponseDict = humanLogic.processRequest(self.fullRequestData, None, jobID=self.jobID, sessionID=self.uuid)
        if humanLogicResponseDict:
            humanLogicResponseDict['logicengine-name'] = humanLogic.getModuleName()
            humanLogicResponseDict['logicengine-class'] = humanLogic.getModuleClass()
            responseArray = []
            responseFound = True
            responseArray.append(humanLogicResponseDict)
        return responseFound, responseArray

    def recalculateResponseContributions(self, responsesSoFar, newResponses):
        # First let's see if we have to add the results to existing ones or
        # add just their contribution-factors. If 'is-master' == 0, we will add only contribution-factors
        # Otherweise, we will add the result itself, thus extending our found items list
        returnResponses = []
        for i, newResponse in enumerate(newResponses):
            isMaster = int(newResponse.get('is-master', 0))
            if isMaster == 1:
                returnResponses.append(newResponse)
            else:
                contributionFactor = float(newResponse.get('contribution-factor', 500.0))
                for j, response in enumerate(responsesSoFar):
                    if str(response['response']) == str(newResponse['response']):
                        responsesSoFar[j]['confidenceLevel'] = float(response['confidenceLevel']) + (float(contributionFactor / 10000.0) / float(i+1))
        returnResponses.extend(responsesSoFar)
        # Now, let's sort them according to their confidenceLevels (highest = 1)
        returnResponses = sorted(returnResponses, key=lambda item: float(item['confidenceLevel']), reverse=True)
        return returnResponses

    def performDataExtraction(self):
        for dE in self.dataExtractors:
            dE.extractDataFromRequest(self.fullRequestData, self.originalQuery, self.uuid)
        
    def run(self):
        responseFound = False
        # Let's make sure we have not yet asked all machines...
        start_time = time.time()
        if self.jobID and self.jobID != "":
            self.responseArray = []
            logging.info('BenderJob: Querying: fullRequest=%s' % json.dumps(self.fullRequestData))
            # Let's first extract data out of the request
            self.performDataExtraction()
	    # Check first in the lookup-cache if we already had this request before...
            if self.taskToPerform == self.PROCESS_REQUEST:
                if self.use_lookup == 1:
                    responseFound, responses = self._checkLookupCache()
                    if responseFound:
                        self.responseArray.extend(responses)
                    # If we couldn't find anything in lookup, check for similarity
                if responseFound == False and self.useSimilarity and self.jobStatus == self.jobStatusWIP:
                    responseFound, responses = self._checkInternalSimilarity()
                    if responseFound:
                        self.responseArray.extend(responses)
                # If we didn't find anything >higherConfidenceLevel so far, ask the primary machines first
                if ((responseFound == False or self.haveResponseAboveConfidenceLevel(self.responseArray, self.hcl) == False) and self.jobStatus == self.jobStatusWIP):
                    responseFound, responses = self._checkPrimaryExternalMachines()
                    if responseFound:
                        self.responseArray = self.recalculateResponseContributions(self.responseArray, responses)
                # If the we still didn't find a response, ask the secondary machines next
                if ((responseFound == False or self.haveResponseAboveConfidenceLevel(self.responseArray, self.hcl) == False) and self.jobStatus == self.jobStatusWIP):
                    responseFound, responses = self._checkSecondaryExternalMachines()
                    if responseFound:
                        self.responseArray = self.recalculateResponseContributions(self.responseArray, responses)
                # Usually, the remaining internal machines can be expensive. Thus we ask them last before going to a human
                if ((responseFound == False or self.haveResponseAboveConfidenceLevel(self.responseArray, self.hcl) == False) and self.jobStatus == self.jobStatusWIP):
                    responseFound, responses = self._checkInternalMachines()
                    if responseFound:
                        self.responseArray = self.recalculateResponseContributions(self.responseArray, responses)
            # If we still don't have a response, ask a human as a last resort (but only if we are supposed to ask a human)
            processing_end_time = time.time()
            if (self.whatToDo == self.AUTOFORWARD_REQUEST or ((responseFound == False or self.haveResponseAboveConfidenceLevel(self.responseArray, self.hcl) == False) and self.jobStatus == self.jobStatusWIP)) and self.use_hli:
                self.jobStatus = self.jobStatusFORWARDED
                responseFound, responses = self._askHumanLogic(self.responseArray)
                if responseFound:
                    self.responseArray = responses
            if responseFound or self.interactive == 1:
                self._processResponse()
            end_time = time.time()
            if self.needsLearning:
                learning_thread = threading.Thread(target=learn_or_retrain, args=(self, self.qToLearn, self.aToLearn, self.qType, self.qCategory, self.mcugAnswers, self.reinforce, self.benderCore))
                learning_thread.start()
                self.needsLearning = False
                self.aToLearn = ''
                self.qToLearn = ''
                self.qType = 'e'
                self.category = 1
                self.mcugAnswers = []
            if self.jobStatus == self.jobStatusWIP or self.jobStatus == self.jobStatusFORWARDED:
                self.jobStatus = self.jobStatusDONE
            if self.finalResponse is not None:
                self.finalResponse['total_time'] = end_time - start_time
                self.finalResponse['hli_time'] = end_time - processing_end_time
                self.finalResponse['processing_time'] = processing_end_time - start_time

    def haveResponseAboveConfidenceLevel(self, responseArray, confidenceLevelThreshold):
        for response in responseArray:
            if float(response['confidenceLevel']) > confidenceLevelThreshold:
                return True
        return False

    def _prepareResponse(self):
        returnResponse = {}
        highestConfidenceLevel = 0.0
        responseArray = self.responseArray
        if responseArray and len(responseArray)>0:
            for response in responseArray:
                responseConfidence = float(response['confidenceLevel'])
                if responseConfidence > highestConfidenceLevel:
                    highestConfidenceLevel = responseConfidence
                    returnResponse = response
            if returnResponse:
                return returnResponse
        return None

    def _processAllResponses(self, responses):
        ret_resps = []
        for r in responses:
            rID = r.get('response', None)
            if rID is None:
                rID = r.get('responseID', None)
            if rID is not None:
                rText = self.indexedResponseProcessor.getIndexedResponses(int(rID))
                newR = dict(r)
                newR['responseText'] = rText
                ret_resps.append(newR)
        return ret_resps

    def _processResponse(self):
        """
        Processes the response found.
        The result is in "self.finalRespons"
        Please note the actual structure of the "finalResponse"
        """
        # First get the guiClientConfig because it may be client, app- or userGroup-Specific answer the 
        # GUI is asking. 
        # In case the mID, channelID and/or userGroupID is set to zero, we set them to NONE and return the
        # DEFAULT answer...
        guiClientConfig = self.benderCore.getGUIClientConfigForSession(self.getUUID())
        mandantID = None
        channelID = None
        userGroupID = None
        if guiClientConfig is not None:
            mandantID = guiClientConfig.get('mID', 0)
            channelID = guiClientConfig.get('channelID', 0)
            userGroupID = guiClientConfig.get('userGroupID', 0)
        if mandantID == 0:
            mandantID = None
        if channelID == 0:
            channelID = None
        if userGroupID == 0:
            userGroupID = None
        response = self._prepareResponse()
        finalResponse = None
        if response and len(response)>0:
            responseFound = True
        else:
            responseFound = False
        if responseFound:
            uqaPID = self.createUQAPID(self.clientID, self.getUUID(), self.jobID)
            finalResponse = {}
            finalResponse.update(response)
            finalResponse['response'] = {
                                    'responseText': response['response'], 
                                    'confidenceLevel': response['confidenceLevel'],
                                    'logicEngineClass' : response['logicengine-class'],
                                    'logicEngineID' : response['logicengine-name'],
                                    'responseType' : 'text',
                                    }
            finalResponse['UUID'] = self.getUUID()
            finalResponse['UQAPID'] = uqaPID
            finalResponse['originalRequestType'] = self.getQueryInputType()
            finalResponse['dateTime'] = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
            finalResponse['authoritative'] = False
            responseIsID = response.get('responseIsID', False)
            if responseIsID:
                responseID = response.get('responseID', None)
                if responseID == None:
                    responseID = response.get('response', None)
                if responseID == None:
                    self.logger.warning('Response is ID but could not find the ID in response...')
                else:
                    rID = int(responseID)
                    original_responses = []
                    if self.interactive == 1:
                        original_responses = self._processAllResponses(self.responseArray)
                    else:
                        original_responses = None
                    responses = self.indexedResponseProcessor.getIndexedResponses(rID)
                    if responses is not None:
                        # A single question may have multiple answers (not now, but maybe in the future :-)
                        if len(responses) > 1:
                            finalResponse['multiResponse'] = True
                        else:
                            finalResponse['multiResponse'] = False
                        # As we have stored whether the GUI wants a client (mandant), app (channel) or userGroup-specific 
                        # answer, we need to extract that specific answer from the answer-types
                        # BEFORE we start post-processing anything
                        # Of course, we could also post-process all of them but since DATAPROVIDERs may need to do
                        # HEAVY LOAD, we don't want to do unnecessary work and post-process only the REALLY RELEVANT
                        # Response...
                        # If the GUI is using this system, it MUST provide a mID, channelID AND userGroupID >0 (ALL MUST EXIST!!!)
                        if mandantID is not None and channelID is not None and userGroupID is not None:
                            mcugKey = 'm{}-c{}-ug{}'.format(mandantID, channelID, userGroupID)
                            mcugAnswer = responses[0]['mcugAnswers'].get(mcugKey, None)
                            if mcugAnswer is None or len(mcugAnswer.strip()) == 0:
                                mcugAsnwer = responses[0]['answer']
                            finalResponse['response']['responseText'] = mcugAnswer
                        else:
                            finalResponse['response']['responseText'] = responses[0]['answer']
                        containsDefinitiveAnswer = False
                        for singleResponse in responses:
                            if singleResponse.get('qType', 'e').lower() == 'e':
                                containsDefinitiveAnswer = True
                                break
                        response['response'] = str(rID) # Let's ALWAYS save this as string ...
                        finalResponse['allResponses'] = responses
                        if self.interactive == 1:
                            finalResponse['interactive_all_responses'] = original_responses
                        finalResponse['authoritative'] = containsDefinitiveAnswer
                    else:
                        responseFound = False
                        finalResponse = {}
            elif response.get('qType', 'e').lower() == 'e':
                finalResponse['authoritative'] = True
        finalResponse['qType'] = response.get('qType', 'e').lower()
        finalResponse['category'] = int(response.get('category', 1))
        questionToLearn = None
        if responseFound == True:
            questionToLearn = self.fullRequestData.get('untouchedOriginalRequest', None)
            # FOR re-training/reinforcement/new-training/lookup-cache:
            #   - If the response was found using original query, we store the original query
            #     as entered by the end-user (no spell-checking, no stop-word removal...
            #   - If the response was found using enriched-query, we store the enriched query
            #     with all typos (NOT spell-checked) and no stop-words removed.
            # This is especially useful for lookup but also useful for our similarity-analysis. In doing
            # any similarity analysis, we automatically remove stop-words, so this should be ok.
            # BUT: the missing spell-checking might be an issue, we need to check that one 
            # TODO: For future, check whether we should store the spell-checked version as non-spell-checked
            #       words may not exist in our word2vec/lsi dictionaries...
            if finalResponse.get('responseIsForEnrichedQuery', 0) == 1 or finalResponse.get('responseIsForEnrichedSpellCheckedQuery', 0) == 1 or finalResponse.get('responseIsForConceptualizedEnrichedQuery', 0) == 1 or finalResponse.get('responseIsForConceptualizedEnrichedSpellCheckedQuery', 0) == 1:
                questionToLearn = self.fullRequestData.get('untouchedEnrichedOriginalRequest', None)

            # Let's figure out how we found the response, i.e., what modified query
            # we used...
            found_using_query_type = None
            for requestKey in self.requestKeys:
                k = self.requestKeys[requestKey][0]
                v = self.requestKeys[requestKey][1]
                if response.get(k, 0) == 1:
                    found_using_query_type = response[v]
                    break
            # If we received the response from the lookup-engine, we
            # - neither store it in Lookup again
            # - nor provide a UQAPID for reinforcementLearning
            # These two functions are reserved for real, machine generated responses only...
            response_generated_by = BenderJobLogger.rgBENDER
            if response['logicengine-class'] == 'lookup':
                # If the response came from lookup-engine, we don't need to store it in lookup again
                # and we don't need to store a reinforcement-training information about it
                finalResponse['response']['originalLogicengineName'] = response['original-logicengine-name']
                finalResponse['response']['originalLogicengineClass'] = response['original-logicengine-class']
                del finalResponse['UQAPID']
            else:
                # Now, first store the request/response for REINFORCEMENT-LEARNING:
                # But only if actually CAME from one of the machines. If it came from a human,
                # We ALREADY assume it to be used for RE-TRAINING
                if response['logicengine-class'] == 'human-logic':
                    finalResponse['response']['originalLogicengineName'] = response.get('original-logicengine-name', '<none>')
                    finalResponse['response']['originalLogicengineClass'] = response.get('original-logicengine-class', '<none>')
                    response_generated_by = BenderJobLogger.rgAGENT
                else:
                    dataToStore = self.fullRequestData['originalRequest'] + "|" + response['response']
                    self.permanentStorage.storeDataForKey(data=dataToStore, key=uqaPID, ownerID="BENDERCORE-UQAPID", timeLimitInSeconds = self.benderCore.getReinforcementTimeout())
                # Next, store request/response into Lookup
                # ... but let's store the correct request for the response otherwise we'll screw up things by:
                #     - either getting wrong responses or
                #     - not getting back anything from lookup at all (waste of space)
                responseJSON = json.dumps(response)
                if found_using_query_type != None:
                    self.lookup.storeRequestAndResponse(found_using_query_type, responseJSON)
            # TODO: If human-logic responded, we still need to do some stuff:
            #   - ALL MACHINES: human selected something from original machine response: re-train that machine
            #   - ALL MACHINES: human ENTERED something new: train ALL machines on new Q/A-data
            #   - DONE: Adding to 'Brain' and 'Similarity'
            if response['logicengine-class'] == 'human-logic':
                if questionToLearn != None:
                    if finalResponse.get('machineResponseSelected', False) == True:
                        self._prepareReLearning(questionToLearn, finalResponse, True)
                    else:
                        self._prepareReLearning(questionToLearn, finalResponse, False)
        dialogShouldBeForgotten = False
        if finalResponse != None:
            self.finalResponse = finalResponse
            containsDefinitiveAnswer = finalResponse.get('authoritative', False)
            logicE = '/'.join([finalResponse['response']['logicEngineClass'], finalResponse['response']['logicEngineID']])
            responseText = finalResponse['response']['responseText']
            rCLevel = finalResponse['response']['confidenceLevel']
            response_found_query = found_using_query_type
            # We need to add the FINAL response POSTPROCESSING in order to add support for
            # DataInfusor-/DataProvider-Support. This is the LAST(!!!) step, everything else is done
            # using un-processed response (i.e., the response as stored in our respose-databases!!!!)
            self.finalResponse['response']['responseText'], containsDefinitiveAnswer = self.responsePostProcessor.processResponse(
                    self.finalResponse['response']['responseText'], 
                    self.dataInfusor,
                    self.dataExtractors,
                    self.dataProviders,
                    self.getUUID(), 
                    response_found_query, 
                    self.fullRequestData['untouchedOriginalRequest'], authoritative=containsDefinitiveAnswer)
            self.finalResponse['authoritative'] = containsDefinitiveAnswer
            if self.interactive != 1:
                if containsDefinitiveAnswer:
                    self.sessionModule.forgetDialog(self.getUUID())
                else:
                    self.sessionModule.storeRequestForSession(self.fullRequestData['untouchedOriginalRequest'], self.getUUID())
        else:
            response_generated_by = BenderJobLogger.rgDELETED
            responseText = None
            rCLevel = 0.0
            logicE = None
            response_found_query = None
        # TODO: Log agentNameOrId as well
        self.job_logger.log_request(self.originalQuery, response_found_query, responseText, self.hcl, self.lcl, rCLevel, logicE, response_generated_by, None)

    def getNewJobID(self):
        self.currentJobNo = self.currentJobNo + 1
        return utils.getUniqueID(self.currentJobNo)

    def _preprocessRequest(self, requestData):
        fullRequestData = None
        queryInputType = requestData['queryInputType']
        requestedResponseType = requestData['requestedResponseType']
        queryText = requestData['queryText']
        if queryInputType == "text":
            queryText = unicode(requestData['queryText'])
            queryText = queryText.strip()
            # In order to show the query and the enriched version to the Human @ HLI,
            # we need to store it as it was sent from the user. For the Machines, we need
            # the stop-word-cleaned, spell-checked version. But for the Human @ HLI, we
            # need it really as it was typed by the end user
            untouchedOriginalRequest = queryText
            if len(untouchedOriginalRequest) > 0:
                fullRequestData = {}
                untouchedEnrichedOriginalRequest = self.sessionModule.enrichRequestInSession(untouchedOriginalRequest, self.getUUID())
                queryText = self.brain.getStopWordCleanedText(queryText)
                self.whatToDo = MLRequestProcessor.PREPROC_PROCESS
		processedQueryText = queryText
                if self.preprocessingModules is not None:
                    for preproc in self.preprocessingModules:
                        processedQueryText, self.whatToDo = preproc.preprocessRequest(processedQueryText, queryText)
                        if self.whatToDo is not MLRequestProcessor.PREPROC_PROCESS:
                            break
                # If we didn't receive any "REJECT" from any preprocessor, we can continue
                # processing the request. Otherwise, we have to reject it (for whatever reason)
                if self.whatToDo != MLRequestProcessor.PREPROC_REJECT:
                    queryText = processedQueryText
                    queryTextSpellChecked = self.spellingModule.getSpellCheckedString(queryText)
                    originalRequest = queryTextSpellChecked
                    fullRequestData['untouchedOriginalRequest'] = untouchedOriginalRequest
                    fullRequestData['untouchedEnrichedOriginalRequest'] = untouchedEnrichedOriginalRequest
                    fullRequestData['originalRequest'] = queryText
                    fullRequestData['spellCheckedRequest'] = queryTextSpellChecked
                    enrichedRequest = self.sessionModule.enrichRequestInSession(untouchedOriginalRequest, self.getUUID())
                    enrichedStopWordRemovedRequest = self.brain.getStopWordCleanedText(enrichedRequest)
                    fullRequestData['enrichedOriginalRequest'] = enrichedStopWordRemovedRequest
                    fullRequestData['enrichedSpellCheckedRequest'] = self.spellingModule.getSpellCheckedString(enrichedStopWordRemovedRequest)
                    request_dict = {'conceptualizedOriginalRequest' : queryText,
                            'conceptualizedSpellCheckedRequest' : queryTextSpellChecked,
                            'conceptualizedEnrichedOriginalRequest': fullRequestData['enrichedOriginalRequest'],
                            'conceptualizedEnrichedSpellCheckedRequest': fullRequestData['enrichedSpellCheckedRequest']}
                    request_dict = self.conceptModule.conceptualizeRequest(request_dict)
                    fullRequestData.update(request_dict)
                    if self.whatToDo == MLRequestProcessor.PREPROC_FORWARD:
                        self.taskToPerform = self.AUTOFORWARD_REQUEST
                else:
                    self.taskToPerform = self.REJECT_REQUEST
                    return None
        else:
            queryURL = requestData['queryURL']
            originalRequest = queryURL
            enrichedRequest = ''
        return fullRequestData

    def setJobData(self, **kwargs):
        self.uuid = kwargs.get('uuid', None)
        self.clientID = kwargs.get('clientID', None)
        self.jobStartTime = datetime.datetime.utcnow()
        self.fullRequestData = self._preprocessRequest(kwargs.get('originalRequestData'))
        if self.fullRequestData is None and self.taskToPerform == self.PROCESS_REQUEST:
            self.logger.warning('BENDERJOB::setJobData: NO REQUEST DATA. Please provide "fullRequestData"')
            return None
        elif self.taskToPerform == self.REJECT_REQUEST:
            self.logger.warning('BENDERJOB::setJobData: Received REJECT_REQUEST for some reason...')
            self.jobStatus = self.jobStatusREJECTED
            return None
        else:
            self.originalRequestData  = kwargs.get('originalRequestData', None)
            self.originalQuery = self.originalRequestData['queryText']
            self.queryInputType = kwargs.get('queryInputType', None)
            # The below is for future use for questions like 'What is on this picture'...
            self.mediaLocation = kwargs.get('mediaLocation', None)
            self.jobOwner = kwargs.get('jobOwner', None)
            self.jobStatus = self.jobStatusWIP
            self.jobID = self.getNewJobID()
            if self.benderCore is not None and self.clientID is not None and self.originalRequestData is not None and self.fullRequestData is not None and self.jobID is not None and (self.getUUID() is not None or self.interactive == 1):
                return self.jobID
            else:
                return None

    def createUQAPID(self, clientID, uuid, jobID):
        return utils.getUniqueID()

    def getJobID(self):
        return self.jobID

    def getJobStartTime(self):
        return self.jobStartTime

    def getOriginalRequest(self):
        return self.fullRequestData['originalRequest']

    def getEnrichedRequest(self):
        return self.enrichedRequest

    def getOriginaRequestData(self):
        return self.orignalRequestData

    def getUUID(self):
        return self.uuid

    def getClientID(self):
        return self.clientID

    def getJobStartTime(self):
        return self.jobStartTime

    def getQueryInputType(self):
        return self.queryInputType

    def getUsedMachineLogics(self):
        return self.usedMachineLogics

    def getUsedDataExtractors(self):
        return self.usedDataExtractors

    def getJobStatus(self):
        return self.jobStatus

    def cancelJob(self):
        self.machineLogicModule.stopAfterCurrentMachine(True)
        self.jobStatus = self.jobStatusKILLED

    def getResponse(self):
        return self.finalResponse

    def getJobOwner(self):
        return self.jobOwner

    def _prepareReLearning(self, q, finalResponse, reinforce=False):
        self.qToLearn = q
        self.aToLearn = finalResponse['response']['responseText']
        self.qType = finalResponse.get('qType', 'e').lower()
        self.mcugAnswers = finalResponse.get('mcugAnswers', {})
        self.qCategory = int(finalResponse.get('category', 1))
        self.reinforce = reinforce
        self.needsLearning = True

