# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import sys 
reload(sys)
sys.setdefaultencoding("utf-8")
import os
import re
from nltk.tokenize import word_tokenize, sent_tokenize

punkt_remover = re.compile(r'[\.,;:\'"/?!@#$%&*()\-_=+\[\]\{\}~`<>`]+')
file_list = []

def multi_sent_tokenize(text, return_as_single_array = False):
    global punkt_remover
    result = []
    if isinstance(text, list):
        aText = ''
        for row in text:
            aText += row + '. '
    else:
        atext = text
    text = punkt_remover.sub('', text)
    for sent in word_tokenize(text):
        if return_as_single_array:
            result.extend(sent)
        else:
            result.append(sent)

    return result


def simple_tokenize(line):
    line = punkt_remover.sub('', line)
    return word_tokenize(line)


