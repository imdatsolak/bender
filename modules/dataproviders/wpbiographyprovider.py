# -*- coding: utf-8 -*-
from __future__ import print_function
import sys 
reload(sys)
sys.setdefaultencoding("utf-8")
import wikipedia

import logging
import os
import json

from modules.dataproviders.mldataprovider import MLDataProvider
"""
Class WPBiographyProvider 
    Wikipedia Biography Provider
    This DataProvider provides biography information about people.
    In order to do so, it connects to Wikipedia, retrieves
    biography information and provides a variable that can then
    be replaced.

    You need to configure which wikipedia to use (language).
    requires 'wikipedia' python package:
        pip install wikipedia


Copyright (c) 2019 Imdat Solak
                All Rights Reserved

Created: 2017-09-28 10:25 CET, ISO

"""
class WPBiographyProvider(MLDataProvider):
    def __init__(self, moduleConfig, configDictionary):
        super(WPBiographyProvider, self).__init__(moduleConfig, configDictionary)
        self.profile = {
                "name" : "wikipedia-biography-provider",
                "class" : "data-provider",
                "supported-languages" : ['de', 'en', 'tr']
                }
        self.module_config = moduleConfig
        self.logger = logging.getLogger(os.path.basename(sys.argv[0]))
        self.biography_language = self.module_config.get('language', 'en')
        if self.biography_language not in self.profile['supported-languages']:
            self.logger.warn('Specified language <{}> not supported. Using <en> instead'.format(self.biography_language))
            self.biography_language = 'en'
        wikipedia.set_lang(self.biography_language)

        self.variables = {
                    'personbiography': { 
                        'required': ['personfullname'],
                        'optional': [],
                        'processor' : self._providePersonBiography,
                        'na-processor' : self._missingPersonFullname
                    }
                }

    def _missingPersonFullname(self, variable, extractedVars):
        return 'Missing full person name'

    def _providePersonBiography(self, variable, extractedVars):
        wikipedia.set_lang(self.biography_language)
        personFullName = extractedVars[self.variables[variable]['required'][0]]
        s = json.dumps(extractedVars)
        result = None
        try:
            result = wikipedia.summary(personFullName)
        except:
            self.logger.info('WPBIOGRAPHYPROVIDER: Could not get anything. PersonFullName = {}, s={}'.format(personFullName, s))

        return result


