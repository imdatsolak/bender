# -*- coding: utf-8 -*-
from __future__ import print_function
import sys 
reload(sys)
sys.setdefaultencoding("utf-8")

from modules.dataproviders.mldataprovider import MLDataProvider
import datetime
"""

"""
class CurrentDateTimeProvider(MLDataProvider):
    def __init__(self, moduleConfig, configDictionary):
        super(CurrentDateTimeProvider, self).__init__(moduleConfig, configDictionary)
        self.profile = {
                "name" : "currentdatetime-provider",
                "class" : "data-provider",
                "supported-languages" : ["de"]
                }
        self.module_config = moduleConfig
        self.variables = {
                    'currenttime': { 
                        'processor': self._getCurrentTime,
                        'na-processor': self.na_value,
                        'required': [],
                        'optional': []
                    },
                    'currentdate': {
                        'processor': self._getCurrentDate,
                        'na-processor': self.na_value,
                        'required': [],
                        'optional': []
                    }
                }

    def na_value(self, variable, extractedVariables):
        return ''

    def _getCurrentTime(self, variable, extractedVariables):
        return datetime.datetime.now().strftime('%H:%M')

    def _getCurrentDate(self, variable, extractedVariables):
        return datetime.datetime.now().strftime('%d.%m.%Y')


