# -*- coding: utf-8 -*-
from __future__ import print_function
import sys 
reload(sys)
sys.setdefaultencoding("utf-8")

import logging
import requests
import json
from core import utils
from modules.mlbendermodule import MLBenderModule

"""
Class MLInternalMachineLogic as described at:
    <none yet>

Copyright (c) 2019 Imdat Solak
            All Rights Reserved

"""
class MLInternalMachineLogicTrainer(MLBenderModule):
    def __init__(self, moduleConfigSection, configDictionary, brain):
        super(MLInternalMachineLogicTrainer, self).__init__(configDictionary)
        self.config_dict = configDictionary
        self.brain = brain
        self.module_config = moduleConfigSection

    def train(self):
        return None

    def reTrain(self):
        return None


class MLInternalMachineLogic(MLBenderModule):
    def __init__(self, moduleConfigSection, configDictionary):
        super(MLInternalMachineLogic, self).__init__(configDictionary)
        self.profile = {
                        "name" : "mlinternalmachine-logic",
                        "class" : "internalmachine-logic"
                        }

    def capabilities(self):
        return self.profile
  
    def initForBender(self, benderInstance):
        self.benderCore = benderInstance

    def performTextQuery(self, originalQuery, num_results=10, jobID=None):
        return None
  
    def performImageQuery(self, query):
        return None, None
  
    def performAudioQuery(self, query):
        return None, None
  
    def performVideoQuery(self, query):
        return None, None
  
    def isMaster(self):
        return False

    def contributionFactor(self):
        return 500

    def reinforceCorrectResponse(self, query, response, inputMediaType, outputMediaType):
        return None, None
  
    def reinforceWrongResponse(self, query, response, inputMediaType, outputMediaType):
        return None, None
  
