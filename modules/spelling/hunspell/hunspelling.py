# *-* coding: utf-8 -*-
from __future__ import print_function
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

import logging
import os
import hunspell
import codecs
import nltk
from core import utils
import gensim
from core.utils import simple_tokenize

from modules.spelling.mlspelling import MLSpelling
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
 
HunSpelling uses 'hunspelling' and 'pyhunspell' for the actual spelling activities. 

Hunspelling:
    http://hunspell.github.io/ --- László Németh (e-mail: nemeth@numbertext.org)

PyHunspell:
    https://github.com/blatinier/pyhunspell (Benoit Latinier)
    https://github.com/blatinier/pyhunspell/blob/master/AUTHORS.md

The dictionaries are usually LibreOffice dictionaries:
    https://extensions.libreoffice.org/
    Licenses: GNU GPL v2 / LGPL v3+

Copyright (c) 2019 Imdat Solak
              All Rights Reserved.
"""

class HunSpelling(MLSpelling):
    def __init__(self, configDictionary):
        super(HunSpelling, self).__init__(configDictionary)
        self.profile = {
                "name" : "hunspelling-module",
                "class": "spelling",
                "supported-languages" : ["de", "en", "tr"]
                } 

        self.logger = logging.getLogger(os.path.basename(sys.argv[0]))
        self.dict_file = utils.getKeyFromSectionInConfiguration('spelling', 'spelling-dict-file', None, configDictionary)
        if self.dict_file == None:
            print('*** Missing spelling-dict-file in configuration. Exiting.')
            sys.exit(1)

        self.aff_file = utils.getKeyFromSectionInConfiguration('spelling', 'spelling-aff-file', None, configDictionary)
        if self.dict_file == None:
            print('*** Missing spelling-aff-file in configuration. Exiting.')
            sys.exit(1)

        self.add_words_file = utils.getKeyFromSectionInConfiguration('spelling', 'training-add-words-from-file', None, configDictionary)

        self.speller = hunspell.HunSpell(self.dict_file, self.aff_file)
        if self.speller == None:
            print('>>>>>> Could not create speller...')
        tokenizer_language = utils.getKeyFromSectionInConfiguration('spelling', 'tokenizer-language', 'german', configDictionary)
        try:
            self.tokenizer = nltk.data.load('tokenizers/punkt/{0}.pickle'.format(tokenizer_language))
        except:
            print('>>>>>> Could not load TOKENIZER language file.')
            sys.exit(1)

        if self.add_words_file != None:
            self.train()

    def train(self):
        print('   | *** SPELLING: Adding additional data to spelling dictionary...')
        wordc = 0
        try:
            all_entries = codecs.open(self.add_words_file, 'r', 'utf-8').readlines()
        except:
            print('| >>>>>> Could not open spelling-additions file...')
            return False

        print('   | +--> Found %d lines ' % len(all_entries))
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
            """
            for word in words:
                errorReturn = self.speller.add(word)
                if errorReturn == 0:
                    wordc += 1
            """
        print('   | *** ... done ... (Added %d words)' %wordc)
        return True

    def checkWordSpelling(self, word):
        return self.speller.spell(word)

    def suggestWord(self, word):
        return self.speller.suggest(word)

    def getSpellCheckedString(self, text):
        words = simple_tokenize(text)
        self.logger.info('MLSpellChecker: SpellChecking: [%s]' % text)
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

    def stemWord(self, word):
        return self.speller.stem(word)

    def addWord(self, word):
        self.stemmer.add(word)

    def addWordsFromText(self, text):
        words = simple_tokenize(text)
        if len(words)>0:
            for word in words:
                self.stemmer.add(word)

