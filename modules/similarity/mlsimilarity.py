# -*- coding: utf-8 -*-
import sys 
reload(sys)
sys.setdefaultencoding("utf-8")

from modules.mlbendermodule import MLBenderModule
"""
Copyright (2019) 2019 Imdat Solak
                All Rights Reserved
"""
class MLSimilarity(MLBenderModule):
    def __init__(self, configDictionary):
        super(MLSimilarity, self).__init__(configDictionary)
        self.profile = {
                "name" : "mlsimilarity-module",
                "class" : "similarity",
                "supported-languages" : ["de"]
                }

    def initForBender(self, benderInstance):
        self.benderCore = benderInstance

    def getSimilarEntriesFromCorpus(self, query, enrichedQuery = '', num_sim = 0):
	return None

    def addNewQAPair(self, questionData, answerData):
	return None
