# *-* coding: utf-8 -*-
from __future__ import print_function
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

import logging
import os
import codecs
import nltk
import gensim
from utils import simple_tokenize

"""
HunSpelling is used for checking spelling of entered text
Usage:
    spelling.checkWordSpelling('krankmeldung') -> True/False
    suggestedWords = spelling.suggestWord('kranckmeldung') -> ['krankmeldung', ...]
    stemmedWords = spelling.stemWord('hauses') -> ['hauses', 'haus']
    spelling.addWord('haushalt') -> True/False
    spell_checked_string = spelling.getSpellCheckedString(aString)
    ...
 
HunSpelling uses 'hunspelling' and 'pyhunspell' for the actual spelling activities. 
On MacOS, we use 'CyHunspell' as the underlying engine:
        - https://pypi.python.org/pypi/CyHunspell
        - https://github.com/OpenGov/cython_hunspell

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
 
Written: 2017-09-25 14:53 CET, ISO
"""
import hunspell

class HunSpelling(object):
    def __init__(self, dict_file, aff_file, add_words_file, tokenizer_language, dictionary_dir=None, language_long = None):

        self.logger = logging.getLogger(os.path.basename(sys.argv[0]))
        self.dict_file = dict_file
        if self.dict_file == None:
            print('*** Missing spelling-dict-file in configuration. Exiting.')
            sys.exit(1)

        self.aff_file = aff_file
        if self.dict_file == None:
            print('*** Missing spelling-aff-file in configuration. Exiting.')
            sys.exit(1)

        self.add_words_file = add_words_file

        if sys.platform == 'darwin':
            localdir = os.path.dirname(__file__)
            dict_dir = os.path.join(localdir, dictionary_dir)
            self.speller = hunspell.Hunspell(language_long, hunspell_data_dir=dict_dir)
        else:
            self.speller = hunspell.HunSpell(self.dict_file, self.aff_file)

        if self.speller == None:
            print('>>>>>> Could not create speller...')

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
                pass
        return True


    def checkWordSpelling(self, word):
        word = word.encode('utf-8')
        return self.speller.spell(word)


    def suggestWord(self, origWord):
        word = origWord.encode('utf-8')
        retval = self.speller.suggest(word)
        if isinstance(retval, basestring):
            return retval
        elif retval is not None and len(retval)>0:
            return retval[0]
        else:
            return origWord


    def getSpellCheckedString(self, text):
        words = simple_tokenize(text)
        spell_checked_text = ''
        for word in words:
            correct_word = word
            if self.checkWordSpelling(word) == False:
                suggested_word = self.suggestWord(word)
                if suggested_word != None and len(suggested_word) > 0:
                    correct_word = suggested_word
            spell_checked_text = spell_checked_text + correct_word + ' '

        spell_checked_text = spell_checked_text.strip()
        return spell_checked_text


    def getSpellCheckedWordList(self, wordList):
        res = []
        for word in wordList:
            correct_word = word
            if self.checkWordSpelling(word) == False:
                suggested_word = self.suggestWord(word)
                if suggested_word != None and len(suggested_word) > 0:
                    correct_word = suggested_word
            res.append(correct_word)
        return res


    def stemWord(self, origWord):
        word = origWord.encode('utf-8')
        stemmedWord = self.speller.stem(word)
        if stemmedWord is not None and len(stemmedWord)>0:
            if not isinstance(stemmedWord, basestring):
                stemmedWord = stemmedWord[0]
        else:
            stemmedWord = origWord
        return stemmedWord


    def stemWordList(self, wordList):
        res = []
        for word in wordList:
            stemmedWord = self.stemWord(word)
            if stemmedWord is None or len(stemmedWord) == 0:
                stemmedWord = word
            res.append(stemmedWord)
        return res


    def addWord(self, word):
        self.stemmer.add(word)
    

    def addWordsFromText(self, text):
        words = simple_tokenize(text)
        if len(words)>0:
            for word in words:
                self.stemmer.add(word)

