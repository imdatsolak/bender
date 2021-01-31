# -*- coding: utf-8 -*-
from __future__ import print_function
import sys 
reload(sys)
sys.setdefaultencoding("utf-8")
import os

import logging
import requests
import json
from core import utils
from modules.mlbendermodule import MLBenderModule

"""
Class MLMachineLogic as described at:

Copyright (c) 2019 Imdat Solak
            All Rights Reserved
"""
class MLMachineLogic(MLBenderModule):
    askPrimaryMachines = 100
    askSecondaryMachines = 200
    askAllMachines = 300

    def __init__(self, configDictionary):
        self.profile = {
                        "name" : "mlmachine-logic",
                        "class" : "machine-logic",
                        "reinforced-learning" : True,
                        "supported-languages" : ["de"],
                        "input-media-types" : ["text"],
                        "output-media-types" : ["text"]
                        }
        machineLogics = utils.getSectionFromConfiguration('machinelogic', [
                                            { 
                                                "name" : "samplenn",
                                                "server_uri" : "http://localhost:9999/api/v1/query",
                                                "accepted_languages" : ["de_DE"], 
                                                "accepted_media_types" : ["text"], 
                                                "returned_media_types" : ["text"],
                                                "returns_response_id" : 1,
                                                "always_ask" : 1
                                            }
                                        ], configDictionary)

        self.shouldStopAfterCurrentMachine = False
        self.primaryMachines = []
        self.secondaryMachines = []
        self.logger = logging.getLogger(os.path.basename(sys.argv[0]))
        for entry in machineLogics:
            if entry.get('always_ask', 0) == 1:
                self.primaryMachines.append(entry)
            else:
                self.secondaryMachines.append(entry)

    def capabilities(self):
        return self.profile
  
    def initForBender(self, benderInstance):
        self.benderCore = benderInstance

    """ 
    This method does the actual querying of all the machine-logic engines running somewhere
    remotely.

    Depending on "machinesToAsk", it will either ask the so-called "primary-machines", i.e.
    those that have a label "alwaysAsk = True" or the secondary machines. It will never 
    ask all of them.

    But it will ask machine-by-machine, collect the responses, put them in an array and then
    return the array.

    If you want it to stop, you send the instance a "stopAfterCurrentMachine(True)". It will
    then, hopefully, stop after the current machine call and return the current
    responses-array.

    What you do with it is up to you. BenderCore discards the result as the Job has been
    killed (from BenderCore's perspective...)
    """
    def performTextQuery(self, query, machinesToAsk):
        self.shouldStopAfterCurrentMachine = False
        responses = []
        requestJSON = { 
                    "queryInputType" : "text",
                    "requestedResponseType" : "text",
                    "queryText" : query
                    }

        if machinesToAsk == self.askPrimaryMachines:
            machinesToAsk = self.primaryMachines
        else:
            machinesToAsk = self.secondaryMachines

        for machine in machinesToAsk:
            machineName = machine['name']
            serverURI = machine['server_uri']
            try:
                serverResponse = requests.post(serverURI, json=requestJSON)
                if serverResponse and serverResponse.status_code == 200:
                    serverResponseJSON = serverResponse.json()
                    serverResponseJSON['logicengine-name'] = machineName
                    serverResponseJSON['logicengine-class'] = 'machine-logic'
                    serverResponseJSON['is-master'] = int(machine.get('is-master', 0))
                    serverResponseJSON['contribution-factor'] = int(machine.get('contriubution-factor', 500))
                    responses.append(serverResponseJSON)
            except:
                self.logger.warning("MLMachineLogic:: Could not connect to machine-logic server: %s at: %s" %(machineName, serverURI))
                pass
            if self.shouldStopAfterCurrentMachine:
                break 

        return responses
  
    def stopAfterCurrentMachine(self, flag):
        self.shouldStopAfterCurrentMachine = flag

    def performImageQuery(self, query):
        return None, None
  
    def performAudioQuery(self, query):
        return None, None
  
    def performVideoQuery(self, query):
        return None, None
  
    def reinforceCorrectResponse(self, query, response, inputMediaType, outputMediaType):
        return None, None
  
    def reinforceWrongResponse(self, query, response, inputMediaType, outputMediaType):
        return None, None
  
