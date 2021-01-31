# *-* coding: utf-8 -*-
from __future__ import print_function
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

import logging
import os
import codecs
import nltk
import enchant
import gensim
from utils import simple_tokenize

"""
EnchantSpelling
Usage:
    spelling.checkWordSpelling('krankmeldung') -> True/False
    suggestedWords = spelling.suggestWord('kranckmeldung') -> ['krankmeldung', ...]
    stemmedWords = ... NOT SUPPORTED WITH ENCHANT / Use HunSpell if you need STEMMING ...
    spelling.addWord('haushalt') -> True/False
    spell_checked_string = spelling.getSpellCheckedString(aString)
    ...
 
EnchantSpelling uses 'Enchant' and 'PyEnchant' for the actual spelling activities. 

Enchant:
    https://github.com/AbiWord/enchant --- Dom Lachowicz

PyEnchant:
    https://pythonhosted.org/pyenchant/ - Ryan Kelly (http://www.rfk.id.au/)

Copyright (c) 2019 Imdat Solak
              All Rights Reserved.
 
Created: 2017-09-25 14:30 CET, ISO - imdat@m-ailabs.bayern

"""

class EnchantSpelling(object):
    def __init__(self, dict_language = 'en', tokenizer_language = 'English', words_file = None):
        self.logger = logging.getLogger(os.path.basename(sys.argv[0]))
        self.dict_language = dict_language
        try:
            self.speller = enchant.Dict(self.dict_language)
        except:
            print('>>>>>>> Could not load language spelling dictionary ', self.dict_language)
            sys.exit(1)

        self.add_words_file = words_file

        try:
            self.tokenizer = nltk.data.load('tokenizers/punkt/{0}.pickle'.format(tokenizer_language))
        except:
            print('>>>>>> Could not load TOKENIZER language file.')
            sys.exit(1)

        if self.add_words_file != None:
            self.train()


    def train(self):
        wordc = 0
        try:
            all_entries = codecs.open(self.add_words_file, 'r', 'utf-8').readlines()
        except:
            return False

        lineno = 0
        for line in all_entries:
            lineno += 1
            line = line.strip()
            try:
                line = line.decode('latin-1')
                errorReturn = self.speller.add(line)
                if errorReturn == 0:
                    wordc += 1
            except:
                print('Ignoring word %s @ lineNo %d' %(line, lineno))
        return True


    def checkWordSpelling(self, word):
        return self.speller.check(word)


    def suggestWord(self, word):
        result = self.speller.suggest(word)
        if result and isinstance(result, list):
            return result[0]
        else:
            return word


    def getSpellCheckedString(self, text):

        words = simple_tokenize(text)
        spell_checked_text = ''
        for word in words:
            correct_word = word
            if self.checkWordSpelling(word) == False:
                suggested_words = self.suggestWord(word)
                if suggested_words != None and len(suggested_words) > 0:
                    s_word = suggested_words[0]
                    correct_word = s_word
            spell_checked_text = spell_checked_text + correct_word + ' '

        spell_checked_text = spell_checked_text.strip()
        return spell_checked_text


    def getSpellCheckedWordList(self, wordList):
        res = []
        for word in wordList:
            correct_word = word
            if self.checkWordSpelling(word) == False:
                suggested_words = self.suggestWord(word)
                if suggested_words != None and len(suggested_words) > 0:
                    s_word = suggested_words[0]
                    correct_word = s_word
            res.append(correct_word)
        return res


    def stemWord(self, word):
        return word


    def stemWordList(self, wordList):
        res = []
        for word in wordList:
            res.append(self.stemWord(word))
        return res


    def addWord(self, word):
        self.speller.add(word)
    

    def addWordsFromText(self, text):
        words = simple_tokenize(text)
        if len(words)>0:
            for word in words:
                self.speller.add(word)


