# -*- coding: utf-8 -*-
import sys 
reload(sys)
sys.setdefaultencoding("utf-8")

from modules.mlbendermodule import MLBenderModule
from core import utils
import os
"""
Class MLIndexedResponseProcessor as described at:

Copyright (c) 2019 Imdat Solak
                All Rights Reserved
"""
class MLIndexedResponseProcessor(MLBenderModule):
    responseStorageTypeStorage = 100
    responseStorageTypeFile = 200
    def __init__(self, configDictionary):
        super(MLIndexedResponseProcessor, self).__init__(configDictionary)
        self.profile = {
                "name" : "mlindexresponseprocessor-module",
                "class" : "indexed-response"
                }

    def initForBender(self, benderInstance):
        self.benderCore = benderInstance

    def getIndexedResponseLocation(self, index):
        """
        Returns the location (URI) of the response. 
        Returns None if there is no such response
        """
        return None

    def getIndexedResponses(self, index):
        return None

    def getIndexedReponseContent(self, index):
        """
        Returns a response, responseMimeType whose index is 'index'
        The response is the full body of the response, i.e., if it's a picture, you get BLOB back.
        Returns also the response mime-type (text/html, text/plain, image/jpeg, ...)
        """
        return None, None

