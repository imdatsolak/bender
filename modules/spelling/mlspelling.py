# *-* coding: utf-8 -*-
from __future__ import print_function
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

from modules.mlbendermodule import MLBenderModule
"""
MLSpelling is used for checking spelling of entered text
Usage:
    spelling = MLSpelling(configDictionary)
    spelling.checkWordSpelling('krankmeldung') -> True/False
    suggestedWords = spelling.suggestWord('kranckmeldung') -> ['krankmeldung', ...]
    stemmedWords = spelling.stemWord('hauses') -> ['hauses', 'haus']
    spelling.addWord('haushalt') -> True/False
    spell_checked_string = spelling.getSpellCheckedString(aString)
    ...
 
MLSpelling is a skeleton class that doesn't do anything (dummy spelling class)

Copyright (c) 2019 Imdat Solak
              All Rights Reserved.
"""

class MLSpelling(MLBenderModule):
    def __init__(self, configDictionary):
        super(MLSpelling, self).__init__(configDictionary)
        self.profile = {
                "name" : "mlspelling-module",
                "class": "spelling",
                "supported-languages" : ["de", "en", "tr"]
                } 

    def train(self):
        return True

    def checkWordSpelling(self, word):
        return True

    def suggestWord(self, word):
        return word

    def getSpellCheckedString(self, text):
        return text

    def stemWord(self, word):
        return word

    def addWord(self, word):
        return

    def addWordsFromText(self, text):
        return

