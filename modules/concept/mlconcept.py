# -*- coding: utf-8 -*-
import sys 
reload(sys)
sys.setdefaultencoding("utf-8")

from modules.mlbendermodule import MLBenderModule
"""
Class MLConcept as described at:

Copyright (c) 2019 Imdat Solak
                All Rights Reserved

Created: 2017-05-13 ??:?? CET, ISO
"""
class MLConcept(MLBenderModule):
    def __init__(self, configDictionary):
        self.profile = {
                "name" : "mlconcept-module",
                "class" : "concept",
                "supported-languages" : ["de"]
                }

    def initForBender(self, benderInstance):
        self.benderCore = benderInstance

    def conceptualizeText(self, text, language='de'):
        return text

    def conceptualizeRequest(self, request, language='de'):
        return request

