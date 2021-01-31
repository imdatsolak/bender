# -*- coding: utf-8 -*-
import sys 
reload(sys)
sys.setdefaultencoding("utf-8")

import spacy
import logging
import os
import types
from core import utils

from modules.nlp.mlnlp import MLNLP
"""
Copyright (c) 2019 Imdat Solak
                All Rights Reserved
"""
class SpacyNLP(MLNLP):
    def __init__(self, configDictionary):
        super(SpacyNLP, self).__init__(configDictionary)
        self.profile = {
                "name" : "spacy-nlp-module",
                "class" : "nlp",
                "supported-languages" : ['de', 'en']
                }
        self.logger = logging.getLogger(os.path.basename(sys.argv[0]))
        self.language = 'de'
        self.module_config = utils.getSectionFromConfiguration('nlp', None, configDictionary)
        if self.module_config is not None:
            self.language_model = self.module_config.get('language_model', 'de_core_news_sm')

        try:
            self.nlp = spacy.load(self.language_model)
        except:
            self.logger.critical('Could not load spaCy language data {}. Please install and re-start'.format(self.language_model))
            os._exit(1)

    def initForBender(self, benderInstance):
        self.benderCore = benderInstance

    def nlp(self, text):
        """
        This is the actual method that does the real work. All other methods
        are usually just short-cuts to this method and return certain attributes of the 
        result of this method
        """
        return self.nlp(text)

    def addWordsToDictionary(self, wordArray):
        """
        Adds new words to its dictionary.
        You use this method when you encounter words in a text that don't exist in the module's dictionary.
        The newly added words are persistent and their indices don't change anymore...
        """
        return True

    def lemmatizeTextWithLanguage(self, text, language):
        """
        Returns a lemmatized version of the text (future versions)
        'language' is the ISO-code (e.g. "de_DE" for German/Germany or "de_CH" for German/Swiss)
        """
        return None

    def universalPOSTagText(self, text):
        """
        Returns a universally POS-tagged version of the text.
        """
        return None
         
    def POSTagTextWithLanguage(self, text, language):
        """
        German, for example, has a peculiar grammar. Other languages may, too. Thus we can
        POS-tag text with different styles (if supported)
        """
        return None
  
    def dependencyArcOfTExtWithLanguage(self, text, language):
        """
        Returns a dependency arc of the text in question based on analyzing it in the given language
        """
        return None

    def calculateSimilarity(self, firstText, secondText):
        """
        Calculates the similarity of two texts based on various algorithms.
        Returns a number between 0.0 (not similar at all) and 1.0 (100% similar)
        """
        return 0.0

    def recognizeEntitiesInText(self, text):
        """
        Recognizes entities in the text and returns an array of entities
        with one entry per recognized entry with the following structure:

            entity = {'label': <labelname>, 'text': <text>, 'start': <startpos>, 'end': <endpos>}

        """
        nlpdoc = self.nlp(text)
        if nlpdoc is None:
            return None
        retval = []
        for nlpent in nlpdoc.ents:
            retval.append({'label': nlpent.label_, 'start': nlpent.start, 'end': nlpent.end, 'text': nlpent.text})
        if len(retval) > 0:
            return retval
        else:
            return None

