# -*- coding: utf-8 -*-
import sys 
reload(sys)
sys.setdefaultencoding("utf-8")

from modules.mlbendermodule import MLBenderModule
"""
Copyright (c) 2019 Imdat Solak
                All Rights Reserved
"""
class MLTextToSpeech(MLBenderModule):
    def __init__(self, configDictionary):
        super(MLTextToSpeech, self).__init__(configDictionary)
        self.profile = {
                "name" : "mltts-module",
                "class" : "tts",
                "supported-languages" : ["de"]
                }

    def initForBender(self, benderInstance):
        self.benderCore = benderInstance


