# -*- coding: utf-8 -*-
from __future__ import print_function

import sys

reload(sys)
sys.setdefaultencoding("utf-8")
"""
    Generate Word2Vec and analyze...
    
    Created: 2017-09-08 08:30 CET, ISO
    """

from gensim import models
import gensim

from stop_words import get_stop_words
import nltk.data
import os as os
import codecs
import logging
import getopt
import json
import re
from utils import simple_tokenize, multi_sent_tokenize
from enchantspelling import EnchantSpelling
from hunspelling import HunSpelling

# Extract tokens from text


punkt_remover = re.compile(r'[.,;:\'"/?!@#$%&*()\-_=+\[\]\{\}~`<>`]+')
def read_all_sentences(top_directory, remove_stop_words=False, stop_words=None, speller=None, stemmer=None):
    sentences = []
    errfile = codecs.open('/tmp/dict-errs.txt', 'w', 'utf-8')
    print('Reading & processing source data... ')
    sys.stdout.flush()
    if remove_stop_words and not stop_words:
        stop_words = get_stop_words('de')
    for root, dirs, files in os.walk(top_directory):
        counter = 0
        files.sort()
        for filename in filter(lambda filename: filename.endswith('.txt'), files):
            counter += 1
            filename = os.path.join(root, filename)
            fContents = codecs.open(filename, 'r', 'utf-8').readlines()
            lineC = len(fContents)
            currL = 0
            for line in fContents:
                if currL % 50 == 0:
                    print('{:-7d}/{:d} Lines processed\r'.format(currL, lineC), end='')
                    sys.stdout.flush()
                currL += 1
                line = unicode(line.strip().lower())
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
                if len(stopped_tokens):
                    sentences.append(stopped_tokens)
    errfile.close()
    print('\ndone')

    return sentences


def generate_word2vec(top_dir, out_dir, lang='de', remove_stop_words=False, speller=None, stemmer=None):
    original_w2v_path = out_dir
    original_w2v_filename = os.path.join(original_w2v_path, 'word2vec_orig.embeddings')
    stop_words = get_stop_words(lang)
    model = None
    if os.path.exists(original_w2v_filename):
        print('Loading Word2Vec model...')
        model = models.Word2Vec.load(original_w2v_filename)
    else:
        print('Generating Word2Vec model...')
        w2v_dim = 2000
        w2v_mc = 2
        w2v_win = 7
        w2v_iter = 50
        w2v_workers = 19 
        sentences = read_all_sentences(top_dir, remove_stop_words, stop_words, speller, stemmer)
        print('\nStarting word2vec generation ...', end='')
        sys.stdout.flush()
        model = models.Word2Vec(sentences, size=w2v_dim, min_count=w2v_mc, iter=w2v_iter, window=w2v_win, workers=w2v_workers)
        original_w2v_path = out_dir
        original_w2v_filename = os.path.join(original_w2v_path, 'word2vec_orig.embeddings')
        model.save(original_w2v_filename)
        fmt_format_name = os.path.join(original_w2v_path, 'w2v.fmt')
        model.wv.save_word2vec_format(fmt_format_name, binary=True)
        print('done (use .fmt for Tensorboard-Projector .tsv-generation if needed)')
    
    return model


def get_most_similar(model, positive, negative, topn, quality):
    if negative == None:
        most_similar = model.wv.most_similar(positive=positive, topn=topn)
    else:
        most_similar = model.wv.most_similar(positive=positive, negative=negative, topn=topn)
    most_similar = sorted(most_similar, key=lambda item: -item[1])
    ms = []
    for entry in most_similar:
        if entry[1] > quality:
            ms.append(entry)
        else:
            break
    new_topics = dict((x, y) for x, y in ms)
    return new_topics


def print_topics(model, topics_file, numtopics, quality, willShowPlot = False, jsonFile = None, printToConsole = False, speller=None, stemmer=None):
    user_topics = {}
    topicsData = list()
    result_data = {}
    
    if not os.path.exists(topics_file):
        print('ERROR: Topics file does not exist.')
        sys.exit(1)
    else:
        print('Performing topics analysis...')
        topics = json.load(codecs.open(topics_file, 'r', 'utf-8'))
        for key in topics.keys():
            topic = topics[key]
            positive = topic['positive']
            negative = topic.get('negative', None)
            if negative is not None:
                negative = [neg.lower() for neg in negative]
            positive = [pos.lower().strip() for pos in positive]

            if speller != None:
                positive = speller.getSpellCheckedWordList(positive)
                if negative is not None:
                    negative = speller.getSpellCheckedWordList(negative)

            if stemmer != None:
                positive = stemmer.stemWordList(positive)
                if negative is not None:
                    negative = stemmer.stemWordList(negative)

            user_topics[key] = dict((k, 1.0) for k in positive)
            
            if len(topic) > 0:
                try:
                    new_topics = get_most_similar(model, positive, negative, 25, 0.4)
                    user_topics[key].update(new_topics)
                    
                    positive.extend(new_topics.keys())
                    new_topics = get_most_similar(model, positive, negative, numtopics, quality)
                    user_topics[key].update(new_topics)
                    
                    new_list = sorted(user_topics[key].iteritems(), key=lambda (k, v): (v, k), reverse=True)
                    user_topics[key] = new_list
                    plotList = [new_list]
                    if willShowPlot:
                        from wordsmap import TopicData
                        topicDataWords = map(lambda item: item[0], plotList[0])
                        oneTopicData = TopicData(key, positive, topicDataWords)
                        topicsData.append(oneTopicData)
                except Exception as e:
                    print(e)
    if printToConsole is True or jsonFile is not None:
        for userKey in user_topics.keys():
            aList = user_topics[userKey]
            resL = []
            for item in aList:
                resL.append(item[0])
            result_data[userKey] = [resL]
    if jsonFile is not None:
        json.dump(result_data, codecs.open(jsonFile, 'w', 'utf-8'), indent=4)
    elif printToConsole is True:
        print(json.dumps(result_data, indent=4))
    return topicsData



def usage():
    print('Missing Parameters.')
    print('Usage: gen2wv.py <-i inputdir> <-o outputdir> <-t initial-topics-file> [-n num-topics] [-s]')
    print('                 [-q <quality>] < -p | -j <jsonFile> | -c > [-s] [--sep] [--imonly] [--speller]')
    print()
    print('\t-i <inputdir>    Directory where the .txt-file is located (source)')
    print('\t-o <outputdir>   Directory where the result should be saved (w2v, etc)')
    print('\t-t <topicsf>     The initial topics-file that you would like to analyze')
    print('\t-n <num-t>       Number of topic-words that you want to extract (default=50)')
    print('\t-q <quality>     Minimum quality of topics (0..1; default=0.65)')
    print('\t-p               Plot the result (interactively, if --sep not given)')
    print('\t-s               Save generated plots')
    print('\t-j <jsonFile>    Write the result to a json-file (for use with wmd_categorize)')
    print('\t-c               Write result to the console')
    print('\t--sep            Create one plot-file per topc')
    print('\t--imonly         Create image only')
    print('\t--speller        Name of spelling/stemming engine to use (\'enchant\' or \'hun\'')
    print('\t--stem           Use HunSpell stemmer to stem words before processing...')
    print()
    print('\tYou can use the result JSON-file in wmd_categorize.py as input and see what it')
    print('\tdelivers. Have fun...')
    sys.exit(1)


def main():
    try:
        options, arguments = getopt.getopt(sys.argv[1:], 'i:o:t:n:q:psj:c', ['indir=', 'outdir=', 'topics=', 'numtopics=', 'quality=', 'plot', 'save', 'sep', 'imonly', 'json', 'console', 'speller=', 'stem'])
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
    outdir = None
    topicsfile = None
    numtopics = 50
    quality = 0.65
    showPlot = False
    save = False
    separate = False
    imagesOnly = False
    jsonFile = None
    printToConsole = False
    speller = None
    stemmer = None
    use_stemmer = False
    for opt, arg in options:
        if opt in ('-p', '--plot'):
            from wordsmap import Plotter, TopicData
            showPlot = True
        if opt in ('-i', '--indir'):
            indir = arg
        elif opt in ('-o', '--outdir'):
            outdir = arg
        elif opt in ('-t', '--topics'):
            topicsfile = arg
        elif opt in ('-n', '--numtopics'):
            numtopics = int(arg)
        elif opt in ('-q', '--quality'):
            quality = float(arg)
        elif opt in ('-s', '--save'):
            '''Save plot images in out directory'''
            save = True
        elif opt in ('--sep'):
            '''Separates topic plots'''
            separate = True
        elif opt in ('--imonly'):
            '''Just save images - doesn't show plot'''
            imagesOnly = True
        elif opt in ('-j', '--json'):
            jsonFile = arg
        elif opt in ('-c', '--console'):
            printToConsole = True
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

    if jsonFile is not None:
        separate = False
        imagesOnly = False
        save = False
        showPlot = False

    if jsonFile is None and showPlot is False and printToConsole is False:
        print('ERROR: Please either request to show a plot (-p) or create a JSON file (-j), alternatively you can also ask the jsonFile to be printed to the console (-c)')
        usage()

    if indir == None or outdir == None or topicsfile == None:
        usage()
    
    if use_stemmer == True:
        if speller != None and isinstance(speller, HunSpelling):
            stemmer = speller
        else:
            stemmer = HunSpelling(hunspell_dict_file, hunspell_aff_file, add_words_file, tokenizer_language, dictionary_dir, language_long)

    model = generate_word2vec(indir, outdir, lang='de', remove_stop_words=remove_stop_words, speller=speller, stemmer=stemmer)
    if model == None:
        print('ERROR: Could not generate model. Something is wrong.')
        sys.exit(1)
    
    topicsData = print_topics(model, topicsfile, numtopics, quality, willShowPlot = showPlot, jsonFile = jsonFile, printToConsole = printToConsole, speller=None, stemmer=stemmer)
    if showPlot:
        Plotter(topicsData, model).showData(save=save, outputDir=outdir, separate=separate, show=(imagesOnly is False))


if __name__ == '__main__':
    if not os.path.exists('logs'):
        os.makedirs('logs')
    logger = logging.getLogger(os.path.basename(sys.argv[0]))
    logging.basicConfig(filename='logs/logfile.log', format='%(asctime)s: %(levelname)s: %(message)s')
    logging.root.setLevel(level=logging.INFO)
    logger.info('**************** NEW Gen2WV SESSION STARTED: %s' % ' '.join(sys.argv))
    main()
