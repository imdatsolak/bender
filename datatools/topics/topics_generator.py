# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import sys 
reload(sys)
sys.setdefaultencoding("utf-8")
import os
import re
import json
import codecs
import getopt
from stop_words import get_stop_words
from utils import multi_sent_tokenize, simple_tokenize
from enchantspelling import EnchantSpelling
from hunspelling import HunSpelling

"""
Training Data Categorization - works in conjunction with topics
"""

file_list = []


def read_documents(top_directory, remove_stop_words=False, stop_words=None, speller=None, stemmer=None):
    topics = {}
    if remove_stop_words and not stop_words:
        stop_words = get_stop_words('de')
    for root, dirs, files in os.walk(top_directory):
        counter = 0
        for dir in dirs:
            topics[dir] = []

        for filename in filter(lambda filename: filename.endswith('.json'), files):
            counter += 1
            filename = os.path.join(root, filename)
            mail = json.load(codecs.open(filename, 'r', 'utf-8'))
            body = mail['body']
            title = mail.get('subject', '')
            fContents = []
            if title != '':
                fContents.append(title)
            fContents.extend(body)
            token_list = []
            for line in fContents:
                line = line.strip().lower()
                tokens = simple_tokenize(line)

                if remove_stop_words is True:
                    stopped_tokens = [i for i in tokens if not i in stop_words]
                else:
                    stopped_tokens = tokens
                stopped_tokens = [token for token in stopped_tokens if len(token)>1]
                if speller != None:
                    stopped_tokens = speller.getSpellCheckedWordList(stopped_tokens)
                if stemmer != None:
                    stopped_tokens = stemmer.stemWordList(stopped_tokens)
                token_list.extend(stopped_tokens)
            file_topic = os.path.basename(os.path.dirname(filename))
            if file_topic in topics.keys():
                topics[file_topic].append(token_list)
    return topics



def analyze_directory(indir, outfile, lang, remove_stop_words, speller, stemmer):
    print('Working... ', end='')
    sys.stdout.flush()
    if remove_stop_words:
        stop_words = get_stop_words(lang)
    topics = read_documents(indir, remove_stop_words, stop_words, speller, stemmer)
    json.dump(topics, codecs.open(outfile, 'w', 'utf-8'), indent=4)
    print('done')



def usage():
    print('Usage:')
    print('\tpython generate_topics.py -i|--indir <in-directory> -o|-outfile <outfile> [--speller <hun|enchant>] [--stem]')
    print()
    print('\t-i <indir>     This is the root directory containing the topics as one subdirectory.')
    print('\t               Each subdirectory contains JSON-Files generated by wmd_...')
    print('\t-o <outfile>   Write result into the <outfile>')
    print('\t--speller      Use either \'hun\'-spell or \'enchant\'-speller (default = no speller)')
    print('\t--stem         Use hunspell\'s stemmer (default = no stemming)')

    sys.exit(1)


if __name__ == '__main__':
    try:
        options, arguments = getopt.getopt(sys.argv[1:], 'i:o:', ['indir=', 'outfile=', 'speller=', 'stem'])
    except getopt.GetoptError:
        usage()

    hunspell_dict_file = 'resources/de_DE.dic'
    hunspell_aff_file = 'resources/de_DE.aff'
    tokenizer_language = 'german'
    language_short = 'de'
    language_long = 'de_DE'
    add_words_file = None
    remove_stop_words = False
    dictionary_dir = 'resources'

    indir = None
    jsonFile = None
    outdir = None
    w2v_file = None
    verbose = False
    outfile = sys.stdout
    outdir = None
    speller = None
    stemmer = None
    use_stemmer = False
    for opt, arg in options:
        if opt in ('-i', '--indir'):
            indir = arg 
        elif opt in ('-o', '--outfile'):
            outfile = arg
        elif opt in ('--speller'):
            spellerName = arg
            if spellerName == 'enchant':
                speller = Enchantspeller(language_short, tokenizer_language, add_words_file)
            elif spellerName == 'hun':
                speller = HunSpelling(hunspell_dict_file, hunspell_aff_file, add_words_file, tokenizer_language, dictionary_dir, language_long)
            else:
                print('ERROR: Unknown speller/speller {}'.format(spellerName))
                usage()
        elif opt in ('--stem'):
            use_stemmer = True

    if indir is None or outfile is None: 
        usage()

    if use_stemmer == True:
        if speller != None and isinstance(speller, HunSpelling):
            stemmer = speller
        else:
            stemmer = HunSpelling(hunspell_dict_file, hunspell_aff_file, add_words_file, tokenizer_language, dictionary_dir, language_long)

    analyze_directory(indir, outfile, language_short, remove_stop_words, speller, stemmer)

