# -*- coding: utf-8 -*-
import sys 
reload(sys)
sys.setdefaultencoding("utf-8")

from modules.mlbendermodule import MLBenderModule
"""
Copyright (c) 2019 Imdat Solak
                All Rights Reserved
"""
class MLSpeechToText(MLBenderModule):
    def __init__(self, configDictionary):
        super(MLSpeechToText, self).__init__(configDictionary)
        self.profile = {
                "name" : "mlstt-module",
                "class" : "stt",
                "supported-languages" : ["de"]
                }

    def initForBender(self, benderInstance):
        self.benderCore = benderInstance


