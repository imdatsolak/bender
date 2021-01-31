# -*- coding: utf-8 -*-
import sys 
reload(sys)
sys.setdefaultencoding("utf-8")

from modules.indexedresponse.mlidxresponseproc import MLIndexedResponseProcessor
from modules.brain.mlbrain import MLBrain
from core import utils
import os
import codecs
"""
Class IndexedResponseProcessor as described at:
    <not there yet>

Copyright (c) 2019 Imdat Solak
                All Rights Reserved
"""
class IndexedResponseProcessor(MLIndexedResponseProcessor):
    def __init__(self, configDictionary):
        super(IndexedResponseProcessor, self).__init__(configDictionary)
        self.profile = {
                "name" : "indexresponseprocessor-module",
                "class" : "indexed-response"
                }

    def getIndexedResponseLocation(self, index):
        """
        Returns the location (URI) of the response. 
        Returns None if there is no such response
        """
        return None

    def getIndexedResponses(self, index):
        """
        Returns a response-array containing all responses as a complete hash:
        returns: 
            [
                {
                    'id': newAnswerID, 
                    'answer': answer, 
                    'mcugAnswers': mcugAnswers
                },
                ...
            ]
        """
        qID = int(index)
        brain = self.benderCore.getBrain()
        return brain.getAnswersForQuestionID(qID)

    def getIndexedReponseContent(self, index):
        """
        Returns a response, responseMimeType whose index is 'index'
        The response is the full body of the response, i.e., if it's a picture, you get BLOB back.
        Returns also the response mime-type (text/html, text/plain, image/jpeg, ...)
        """
        qID = int(index)
        brain = self.benderCore.getBrain()
        response = brain.getAnswerTextsForQuestionID(qID)
        if response:
            return '\n'.join(response).strip(), 'text/plain'
        else:
            return None, None

