# *-* coding: utf-8 -*-
from __future__ import print_function
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
from modules.mlbendermodule import MLBenderModule


"""
A superclass for all training module classes.

Copyright (C) 2019 Imdat Solak
                All Rights Reserved
"""
class MLBenderTrainingModule(MLBenderModule):
    def __init__(self, brain, configDictionary):
        super(MLBenderTrainingModule, self).__init__(configDictionary)
        self.profile = { 
                    "name" : "mlbender-training-module",
                    "class" : "generic-training-module"
                }   

    def train(self):
        return True

    def reTraing(self):
        return

