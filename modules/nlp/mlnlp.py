# -*- coding: utf-8 -*-
import sys 
reload(sys)
sys.setdefaultencoding("utf-8")

from modules.mlbendermodule import MLBenderModule
"""
Copyright (c) 2019 Imdat Solak
                All Rights Reserved
"""
class MLNLP(MLBenderModule):
    def __init__(self, configDictionary):
        super(MLNLP, self).__init__(configDictionary)
        self.profile = {
                "name" : "mlnlp-module",
                "class" : "nlp",
                "supported-languages" : ["de"]
                }

    def initForBender(self, benderInstance):
        self.benderCore = benderInstance

    def nlp(self, text):
        """
        This is the actual method that does the real work. All other methods
        are usually just short-cuts to this method and return certain attributes of the 
        result of this method
        """
        return None

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
        return None

