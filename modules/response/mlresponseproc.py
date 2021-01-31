# -*- coding: utf-8 -*-
import sys 
reload(sys)
sys.setdefaultencoding("utf-8")

from modules.mlbendermodule import MLBenderModule
from core import utils
"""
Copyright (c) 2019 Imdat Solak
                All Rights Reserved
"""
class MLResponseProcessor(MLBenderModule):
    responseStorageTypeStorage = 100
    responseStorageTypeFile = 200
    def __init__(self, configDictionary):
        super(MLResponseProcessor, self).__init__(configDictionary)
        self.profile = {
                "name" : "mlresponseprocessor-module",
                "class" : "response-postprocessor"
                }

    def initForBender(self, benderInstance):
        self.benderCore = benderInstance

    def processResponse(self, response, infusor, extractors, providers, session, request, originalRequest, authoritative=True):
        return infusor.infuseDataToResponse(response, extractors, providers, session, request, originalRequest, authoritative)
