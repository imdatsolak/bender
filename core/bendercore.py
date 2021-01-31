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
from gensim import corpora
from time import sleep
from core import utils
from core.benderjob import BenderJob
from core.benderjob import BenderJobLogger
from modules.machinelogic.imachinelogic.mlimachinelogic import MLInternalMachineLogic
from modules.mlbendermodule import MLBenderModule
from modules.concept.mlconcept import MLConcept
from modules.dataextractors.mldataextractor import MLDataExtractor
from modules.datainfusor.mldatainfusor import MLDataInfusor
from modules.dataproviders.mldataprovider import MLDataProvider
from modules.humanlogic.mlhumanlogic import MLHumanLogic
from modules.lookup.mllookup import MLLookup
from modules.machinelogic.mlmachinelogic import MLMachineLogic
from modules.nlp.mlnlp import MLNLP
from modules.session.mlsession import MLSession
from modules.speech.mlstt import MLSpeechToText
from modules.speech.mltts import MLTextToSpeech
from modules.storage.mlstorage import MLStorage
from modules.storage.transientstorage.mltransientstorage import MLTransientStorage
from modules.storage.permanentstorage.mlpermanentstorage import MLPermanentStorage
from modules.indexedresponse.mlidxresponseproc import MLIndexedResponseProcessor
from modules.response.mlresponseproc import MLResponseProcessor
from modules.similarity.mlsimilarity import MLSimilarity
from modules.brain.mlbrain import MLBrain
from modules.spelling.mlspelling import MLSpelling
from modules.requestproc.mlreqproc import MLRequestProcessor



class BenderSecurity:
    def __init__(self):
        self.clients = ['batchTestClient', 'imdatChat'];

    def isClientAllowed(self, requestData):
        clientID = requestData['clientID']
        return clientID in self.clients

"""
This is main Bender class as documented at:
         https://wiki.m-ailabs.com/display/DJ/Bender+Engine

Usage:
        from core.bendercore import BenderCore
        bender = BenderCore(configDictionary)
        ...
 
Copyright (c) 2019 Imdat Solak
          All Rights Reserved.
 
Created: 2017-04-14 14:00 CET, ISO

TODO: All modules should also get their own configuration sections in a separate parameter during init...

"""
LOG_FORMAT='%(asctime)s: %(levelname)s: %(message)s'
class BenderCore:
    def __init__(self, configDictionary):
        self.configuration = configDictionary
        self.security = BenderSecurity()
        logFile = utils.getKeyFromSectionInConfiguration('bender-core', 'bender_core_logfile', 'logs/bender-core.log', configDictionary)
        utils.safe_create_directory(os.path.dirname(logFile))
        logging.basicConfig(level=logging.WARNING, filename=logFile + '.libs.log', format=LOG_FORMAT)
        self.logger = logging.getLogger(os.path.basename(sys.argv[0]))
        loggingFileHandler = logging.FileHandler(logFile)
        loggingFileHandler.setLevel(logging.INFO)
        loggingMemoryHandler = logging.handlers.MemoryHandler(128, target=loggingFileHandler)
        loggingMemoryHandler.setLevel(logging.INFO)
        loggingFormatter = logging.Formatter(LOG_FORMAT)
        self.logger.addHandler(loggingMemoryHandler)
        loggingFileHandler.setFormatter(loggingFormatter)
        loggingMemoryHandler.setFormatter(loggingFormatter)
        self.logger.setLevel(logging.INFO)
        self.logger.info('###################### STARTING A NEW BENDER INSTANCE #######################')
        self.logger.info('running %s' % ' '.join(sys.argv))
        self.interactive = int(utils.getKeyFromSectionInConfiguration('bender-core', 'interactive', 0, configDictionary))
        self.num_results = int(utils.getKeyFromSectionInConfiguration('bender-core', 'num_results', 1, configDictionary))
        self.use_hli = int(utils.getKeyFromSectionInConfiguration('bender-core', 'use_hli', 1, configDictionary))
        self.use_lookup = int(utils.getKeyFromSectionInConfiguration('bender-core', 'use_lookup', 1, configDictionary))
        self.name = utils.getKeyFromSectionInConfiguration('bender-core', 'name', 'Bender', configDictionary)
        self.personality = utils.getKeyFromSectionInConfiguration('bender-core', 'personality', 'mail-responder', configDictionary)
        self.lowerCL = float(utils.getKeyFromSectionInConfiguration('bender-core', 'lowerconfidence_level', 0.85, configDictionary))
        self.higherCL = float(utils.getKeyFromSectionInConfiguration('bender-core', 'higherconfidence_level', 0.95, configDictionary))
        self.reinforcementTimeout = int(utils.getKeyFromSectionInConfiguration('bender-core', 'reinforcement_timeout', 7 * 24 * 60 * 60, configDictionary))
        self.useSimilarity = int(utils.getKeyFromSectionInConfiguration('bender-core', 'use_similarity', 1, configDictionary))
        
        transient_storage = utils.getModulenameFromConfiguration('transientstorage', 'modules.storage.transientstorage.MLTransientStorage', configDictionary)
        permanent_storage = utils.getModulenameFromConfiguration('permanentstorage', 'modules.storage.permanentstorage.MLPermanentStorage', configDictionary)
        lookup = utils.getModulenameFromConfiguration('lookup', 'modules.lookup.mllookup.MLLookup', configDictionary)
        session = utils.getModulenameFromConfiguration('session', 'modules.session.mlsession.MLSession', configDictionary)
        nlp = utils.getModulenameFromConfiguration('nlp', 'modules.nlp.mlnlp.MLNLP', configDictionary)
        humanLogic = utils.getModulenameFromConfiguration('humanlogic', 'modules.humanlogic.mlhumanlogic.MLHumanLogic', configDictionary)
        concept = utils.getModulenameFromConfiguration('concept', 'modules.concept.mlconcept.MLConcept', configDictionary)
        stt = utils.getModulenameFromConfiguration('stt', 'modules.speech.mlstt.MLSTT', configDictionary)
        tts = utils.getModulenameFromConfiguration('tts', 'modules.speech.mltts.MLTTS', configDictionary)
        responseProcessor = utils.getModulenameFromConfiguration('response-postprocessor', 'modules.response.mlresponseproc.MLResponseProcessor', configDictionary)
        dataInfusor = utils.getModulenameFromConfiguration('datainfusor', 'modules.datainfusor.mldatainfusor.MLDataInfusor', configDictionary)
        similarity = utils.getModulenameFromConfiguration('similarity', 'module.similarity.mlsimilarity.MLSimilarity', configDictionary)
        indexedResponseProc = utils.getModulenameFromConfiguration('indexed-response-processor', 'module.response.mlidxresponseproc.MLIndexedResponseProcessor', configDictionary)
        brain = utils.getModulenameFromConfiguration('brain', 'modules.brain.mlbrain.MLBrain', configDictionary)
        spelling = utils.getModulenameFromConfiguration('spelling', 'modules.spelling.mlspelling.MLSpelling', configDictionary)

        utils.validate_module_class(transient_storage, MLTransientStorage)
        self.transientStorage = utils.initialize_class(transient_storage, configDictionary)

        utils.validate_module_class(permanent_storage, MLPermanentStorage)
        self.permanentStorage = utils.initialize_class(permanent_storage, configDictionary)

        utils.validate_module_class(lookup, MLLookup)
        self.lookup = utils.initialize_class(lookup, configDictionary)

        utils.validate_module_class(session, MLSession)
        self.session = utils.initialize_class(session, configDictionary)

        utils.validate_module_class(nlp, MLNLP)
        self.nlp = utils.initialize_class(nlp, configDictionary)

        utils.validate_module_class(humanLogic, MLHumanLogic)
        self.humanLogic = utils.initialize_class(humanLogic, configDictionary)
        self.humanLogicClass = humanLogic

        utils.validate_module_class(concept, MLConcept)
        self.concept = utils.initialize_class(concept, configDictionary)

        utils.validate_module_class(stt, MLSpeechToText)
        self.stt = utils.initialize_class(stt, configDictionary)

        utils.validate_module_class(tts, MLTextToSpeech)
        self.tts = utils.initialize_class(tts, configDictionary)

        utils.validate_module_class(dataInfusor, MLDataInfusor)
        self.dataInfusor = utils.initialize_class(dataInfusor, configDictionary)

        utils.validate_module_class(responseProcessor, MLResponseProcessor)
        self.responseProcessor = utils.initialize_class(responseProcessor, configDictionary)

        utils.validate_module_class(similarity, MLSimilarity)
        self.similarity = utils.initialize_class(similarity, configDictionary)

        utils.validate_module_class(indexedResponseProc, MLIndexedResponseProcessor)
        self.indexedResponseProcessor = utils.initialize_class(indexedResponseProc, configDictionary)

        utils.validate_module_class(brain, MLBrain)
        self.brain = utils.initialize_class(brain, configDictionary)

        utils.validate_module_class(spelling, MLSpelling)
        self.spelling = utils.initialize_class(spelling, configDictionary)

        self.machineLogic = MLMachineLogic(configDictionary)

        # NOTE: Even though we try to instantiate the classes in the right order
        # and try to call their 'initForBender' in the right order, you should NEVER, in your module
        # depend on any of the modules being already initialized in your implementation of these two
        # methods:
        #       __init__
        #       initForBender
        # Instead, you should request any other module instance only when you actually need them
        # during the processing of data
        #
        # The only exception is MLBrain that relies on concept and nlp being already initialized before
        # itself is called ... and this only during training...
        self.permanentStorage.initForBender(self)
        self.transientStorage.initForBender(self)
        self.nlp.initForBender(self)
        self.concept.initForBender(self)
        self.brain.initForBender(self)
        self.lookup.initForBender(self)
        self.session.initForBender(self)
        self.humanLogic.initForBender(self)
        self.stt.initForBender(self)
        self.tts.initForBender(self)
        self.dataInfusor.initForBender(self)
        self.responseProcessor.initForBender(self)
        self.similarity.initForBender(self)
        self.indexedResponseProcessor.initForBender(self)
        self.machineLogic.initForBender(self)
        self.spelling.initForBender(self)
        self.dataProviders = [] 
        dataproviders = utils.getSectionFromConfiguration('dataproviders', [ 'modules.dataproviders.mldataprovider.MLDataProvier' ], configDictionary)
        for dp in dataproviders:
            module = dp['module']
            utils.validate_module_class(module, MLDataProvider)
            newInstance = utils.initialize_class_with_config_section(module, dp, configDictionary)
            newInstance.initForBender(self)
            self.dataProviders.append(newInstance)
        self.dataExtractors = [] 
        dataextractors = utils.getSectionFromConfiguration('dataextractors', [ 'modules.dataextractors.mldataextrator.MLDataExtractor' ], configDictionary)
        for de in dataextractors:
            module = de['module']
            utils.validate_module_class(module, MLDataExtractor)
            newInstance = utils.initialize_class_with_config_section(module, de, configDictionary)
            newInstance.initForBender(self)
            self.dataExtractors.append(newInstance)
        self.internalMachineLogics = [] 
        internalMLs = utils.getSectionFromConfiguration('i-machinelogic', None, configDictionary)
        for iml in internalMLs:
            module = iml['module']
            utils.validate_module_class(module, MLInternalMachineLogic)
            newInstance = utils.initialize_class_with_config_section(module, iml, configDictionary)
            newInstance.initForBender(self)
            self.internalMachineLogics.append(newInstance)
        self.preprocessors = [] 
        preprocs = utils.getSectionFromConfiguration('preprocessors', None, configDictionary)
        for preproc in preprocs:
            module = preproc['module']
            utils.validate_module_class(module, MLRequestProcessor)
            newInstance = utils.initialize_class_with_config_section(module, preproc, configDictionary)
            newInstance.initForBender(self)
            self.preprocessors.append(newInstance)
        self.jobData = {}
        self.sessionData = {}
        self.configuration = configDictionary
        self.dataInfusor.setDataExtractorsAndProviders(self.dataExtractors, self.dataProviders)
        self.benderjob_logger = BenderJobLogger(configDictionary)

    def benderConfiguration(self):
        return self.configuration, 200

    def clientAllowed(self, requestData):
        return self.security.isClientAllowed(requestData)

    def heartbeat(self):
        return {'heartbeat' : 'I am alive!!!'}, 200

    def currentSessionForUUID(self, UUID):
        # Returns the current session ID for the UUID given
        return False  
  
    def qaPairForQAPID(self, qaPID):
        # Returns the Question-/Answer-Pair from the persistent storage (if it exists)
        # returns two values if it exists (question, answer)
        # returns nil if doesn't exist
        return False  

    def getGUIClientConfigForSession(self, sessionID):
        # Returns the GUI Clients Configuration information
        return self.transientStorage.dataForKey('guiClientConfig:' + sessionID)

    def newSession(self, requestData):
        clientID = requestData['clientID']
        if self.security.isClientAllowed(requestData):
            newUUID = self.session.newSession(clientID)
            if newUUID:
                self.sessionData[newUUID] = clientID
                self.transientStorage.storeDataForKey(requestData, 'guiClientConfig:' + newUUID)
                return {"UUID": newUUID}, 200
            else:
                return {}, 503
        return {}, 401

    # The following is a call-back from session when a session has expired.
    # Session itself checks whether it expires. In such a case, it will remove
    # all session relevant data and call back BenderCore to tell that it has
    # expired...
    def sessionExpired(self, uuid):
        if uuid in self.sessionData.keys():
            self.transientStorage.deleteDataForKey('guiClientConfig:'+uuid)
            del self.sessionData[uuid]

    def deleteSession(self, requestData):
        if self.security.isClientAllowed(requestData):
            uuid = requestData['UUID']
            clientID = requestData['clientID']
            if uuid in self.sessionData.keys() and self.sessionData.get(uuid, None) == clientID:
                if self.session.endSession(uuid):
                    self.transientStorage.deleteDataForKey('guiClientConfig:'+uuid)
                    return {}, 200
                else:
                    return {}, 503
            else:
                return {}, 404
        return {}, 401

    def performRequest(self, requestData):
        if self.security.isClientAllowed(requestData):
            clientID = requestData['clientID']
            uuid = requestData.get('UUID', '')
            if self.interactive == 1 or uuid in self.sessionData.keys():
                queryInputType = requestData['queryInputType']
                requestedResponseType = requestData['requestedResponseType']
                queryText = requestData['queryText']
                if len(queryText) == 0:
                    return {}, 400
                threadID = len(self.jobData) + 1
                newJob = BenderJob(threadID, self, useSimilarity=self.useSimilarity, jobLogger=self.benderjob_logger, interactive=self.interactive, use_hli=self.use_hli, num_results=self.num_results, use_lookup=self.use_lookup)
                newJobID = newJob.setJobData(uuid=uuid, clientID=clientID, originalRequestData=requestData, queryInputType=queryInputType, jobOwner=clientID)
                if newJobID:
                    self.jobData[newJobID] = newJob
                    newJob.start()
                    if self.interactive == 1:
                        jStatus = newJob.getJobStatus()
                        while jStatus != BenderJob.jobStatusREJECTED and jStatus != BenderJob.jobStatusKILLED and jStatus != BenderJob.jobStatusDONE:
                            sleep(0.1)
                            jStatus = newJob.getJobStatus()
                        if jStatus == BenderJob.jobStatusDONE:
                            result = self.getResponse({'jobID' : newJobID, 'clientID' : clientID })
                        else:
                            result = {}
                        return result, 200
                    else:
                        return {"jobID" : newJobID, "estimatedTimeInSeconds": 102410241024}, 200
                elif newJob.getJobStatus() == BenderJob.jobStatusREJECTED:
                    return {}, BenderJob.jobStatusREJECTED
                else:
                    return {}, 503
            else:
                return {}, 412
        else:
            return {}, 401

    def jobStatus(self, requestData):
        if self.security.isClientAllowed(requestData):
            jobID = requestData['jobID']
            clientID = requestData['clientID']
            if jobID in self.jobData:
                theJob = self.jobData[jobID]
                if theJob.getJobOwner() == clientID:
                    jobStatus = theJob.getJobStatus()
                    if jobStatus == BenderJob.jobStatusREJECTED or jobStatus == BenderJob.jobStatusKILLED:
                        del self.jobData[jobID]
                    return {}, jobStatus
                else:
                    return {}, 401
            else:
                return {}, 404
        return {}, 401

    def deleteJob(self, requestData):
        if self.security.isClientAllowed(requestData):
            jobID = requestData['jobID']
            clientID = requestData['clientID']
            if jobID in self.jobData:
                theJob = self.jobData[jobID]
                if theJob.getJobOwner() == clientID:
                    theJob.cancelJob()
                    del self.jobData[jobID]
                    return {}, 200
                else:
                    return {}, 401
            else:
                return {}, 404
        return {}, 401

    def getResponse(self, requestData):
        if self.security.isClientAllowed(requestData):
            jobID = requestData['jobID']
            clientID = requestData['clientID']
            responseFound = False
            if jobID in self.jobData:
                theJob = self.jobData[jobID]
                if theJob.getJobOwner() == clientID:
                    finalResponse = theJob.getResponse()
                    jobStatus = theJob.getJobStatus()
                    self.logger.info('*** BENDER-CORE: Return to caller...')
                    del self.jobData[jobID]
                    if jobStatus == BenderJob.jobStatusDONE and finalResponse is not None and len(finalResponse.keys())>0:
                        return finalResponse, 200
                    elif jobStatus != BenderJob.jobStatusDONE:
                        return {}, jobStatus
                    else:
                        return {}, 204
                else:
                    return {}, 401
            else:
                return {}, 404
        return {}, 401

    def reinforceLearning(self, requestData):
        return {}, 501
 
    def lowerConfidenceLevel(self):
        return self.lowerCL

    def higherConfidenceLevel(self):
        return self.higherCL

    def hliList(self, requestData):
        return self.humanLogic.getListOfJobs(requestData['agentNameOrID'])

    def hliLockItem(self, requestData):
        return self.humanLogic.lockJob(requestData['requestID'], requestData['agentNameOrID'])

    def hliDeleteItem(self, requestData):
        return self.humanLogic.deleteJob(requestData['requestID'], requestData['reason'], requestData['agentNameOrID'])

    def hliUnlockItem(self, requestData):
        return self.humanLogic.unlockJob(requestData['requestID'], requestData['agentNameOrID'])

    def hliAnswerItem(self, requestData):
        return self.humanLogic.answerJob(requestData)

    def addNewQAPairToMachines(self, indexedQ, indexedA):
        # TODO: This needs to be fixed for future use for all machines.
        #       Since we only have "Internal Machine Logics" (iML), this is ok for now
        for iml in self.internalMachineLogics:
            iml.reinforceCorrectResponse(indexedQ, indexedA, 'text/plain', 'text/plain')
        return True

    # ##################################################################
    # Module-related functionality...
    # ##################################################################
    def storageModule(self):
        return self.permanentStorage

    def transientStorageModule(self):
        return self.transientStorage

    def nlpModule(self):
        return self.nlp  

    def conceptModule(self):
        return self.concept  

    def sessionModule(self):
        return self.session  

    def dataProviderModules(self):
        return self.dataProviders

    def dataExtractorModules(self):
        return self.dataExtractors

    def dataInfusorModule(self):
        return self.dataInfusor

    def lookupModule(self):
        return self.lookup  

    def sttModule(self):
        return self.stt  

    def ttsModule(self):
        return self.tts  

    def humanLogicModule(self):
        return self.humanLogic  

    def newHumanLogicInstance(self):
        newHumanLogicI = utils.initialize_class(self.humanLogicClass, self.configuration)
        newHumanLogicI.initForBender(self)
        return newHumanLogicI

    def machineLogic(self):
        return self.machineLogic  

    def responseProcessorModule(self):
        return self.responseProcessor

    def indexedResponseProcessorModule(self):
        return self.indexedResponseProcessor

    def similarityModule(self):
        return self.similarity

    def newMachineLogic(self):
        return MLMachineLogic(self.configuration)

    def preprocessingModules(self):
        return self.preprocessors

    def spellingModule(self):
        return self.spelling

    def getBrain(self):
        return self.brain

    def internalMachineLogicModules(self):
        return self.internalMachineLogics

    def getDictionary(self):
        return self.brain.getDictionary()

    def getReinforcementTimeout(self):
        return self.reinforcementTimeout

    class InvalidModuleException(Exception):
        """
        An exception to be raised when an adapter of an unexpected class type is recieved.
        """

        def __init__(self, value='Recieved an unexpected adapter setting.'):
            self.value = value

        def __str__(self):
            return repr(self.value)


