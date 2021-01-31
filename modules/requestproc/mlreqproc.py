# -*- coding: utf-8 -*-
import sys 
reload(sys)
import datetime
sys.setdefaultencoding("utf-8")

from core import utils
from modules.mlbendermodule import MLBenderModule
"""
Copyright (c) 2019 Imdat Solak
                All Rights Reserved

Created: 2018-01-03 09:32 CET, ISO
"""
class MLRequestProcessor(MLBenderModule):
    PREPROC_REJECT = 100
    PREPROC_FORWARD = 200
    PREPROC_PROCESS = 1000
    def __init__(self, moduleConfig, configDictionary):
        super(MLRequestProcessor, self).__init__(configDictionary)
        self.profile = {
                "name" : "mlreqproc-module",
                "class" : "request-processor"
                }
        self.module_config = moduleConfig
        self.config_dict = configDictionary

    def capabilities(self):
        return self.profile
  
    def preprocessRequest(self, request, originalRequest):
        """
        Pre-processes the request
        'request' is the request that may have already been preprocessed by another
                  pre-processor
        'originalRequest' is the request as it came from the API, i.e., it has not been
                  pre-processed by any other pre-processor yet

        Returns two values:
            - the pre-processed request (in this case just the one we have received)
            - either PREPROC_PROCESS, PREPROC_FORWARD or PREPROC_REJECT
        """
        return request, self.PREPROC_PROCESS

