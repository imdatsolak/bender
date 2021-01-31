# -*- coding: utf-8 -*-
from __future__ import print_function
import sys 
reload(sys)
sys.setdefaultencoding("utf-8")
"""
GenSimModelGenerator - incl. class GenSimModel and auxiliary classes & functions
Copyright (c) 2019 Imdat Solak
Copyright (c) 2014 Mohamed Sordo <mohamed.sordo@gmail.com>
                         http://msordo.weebly.com/
All rights reserved.

GenSimModel is partially based on "class model" from Mohamed Sordo, but significantly
altered and bug-fixed to adapt to multi-file reading/comparing.

TfIfd index & similarity code is (c) 2017 M-AIOLABS, written by Imdat Solak (ISO)
doc2id / id2doc completely rewritten to support multi-document dictionaries, (c) 2017 M-AILABS, written by ISO
As a 'side effect', this class also generates the word2vec embed file that is required by
our neuronal networks

"""

import pickle
import numpy
from gensim import corpora, models, similarities, models, matutils
import gensim

from nltk.tokenize import RegexpTokenizer
from stop_words import get_stop_words
from nltk.stem.porter import PorterStemmer
import nltk.data
from core.progressbar import ProgressBar, Percentage, Bar, ETA, FormatLabel, AnimatedMarker
from core import utils
import os as os
import pandas as pd
import re
import codecs
import itertools
from functools import wraps
from six import string_types
import logging
from core.gensim_utils import cosine
from modules.brain.mlbrain import MLBrain, TrainingCorpus, convert_train_data


# Extract tokens from text
wordTokenizer = RegexpTokenizer(u'\w+')
sentenceTokenizer = nltk.data.load('tokenizers/punkt/english.pickle')

# Get a list of common German words that can be removed from tokens
en_stop = get_stop_words('de')
# Add additional words if neccessary to remove noisy information in SSD Config

def read_all_sentences(top_directory, remove_stop_words=True, stop_words=None):
    """
    Iterate over all documents, yielding a document (=list of utf8 tokens) at a time.
    Updated: 2016-12-29 13:28 CET, ISO
             Fixed so many bugs, unbelievable :-()
    """
    global sentenceTokenizer
    global wordTokenizer
    sentences = []
    errfile = codecs.open('/tmp/dict-errs.txt', 'w', 'utf-8')
    if remove_stop_words and not stop_words:
        stop_words = get_stop_words('en')
    for root, dirs, files in os.walk(top_directory):
        counter = 0
        widgets=[FormatLabel('   | File: %(message)s [%(value)s/'+str(len(files))+']'), ' ', Percentage(), ' ', Bar(marker='@', left='[', right=']'), ' ', ETA()]
        pBar = ProgressBar(widgets=widgets, maxval=len(files)).start()
        files.sort()
        for filename in filter(lambda filename: filename.endswith('.txt'), files):
            counter += 1
            pBar.update(counter, filename)
            filename = os.path.join(root, filename)
            fContents = codecs.open(filename, 'r', 'utf-8').read() # read the entire file as a large string
            fContents = ' '.join(fContents.split('\n'))
            contents = sentenceTokenizer.tokenize(fContents)
            for content in contents:
                content = content.lower() 
                try:
                    tokens = wordTokenizer.tokenize(content)
                    if remove_stop_words is True:
                        stopped_tokens = [i for i in tokens if not i in stop_words]
                    else:
                        stopped_tokens = tokens
                    sentences.append(stopped_tokens)
                except:
                    print('Token error in file [', filename, ']', file=errfile)
        pBar.finish()
    errfile.close()
    return sentences


class GenSimModelGenerator:
    def __init__(self, brain, configDict):
        self.config_dict = configDict
        self.dict_source_dir = utils.getKeyFromSectionInConfiguration('bender-training', 'dictionary_data_source_path', None, configDict)
	self.train_data_source_dir = utils.getKeyFromSectionInConfiguration('bender-training', 'converted_train_data_q_path', None, configDict)
        self.num_topics = int(utils.getKeyFromSectionInConfiguration('bender-training', 'num_topics_lsi', 200, configDict))
        self.output_root_path = utils.getKeyFromSectionInConfiguration('bender-training', 'output_path', None, configDict)
        self.dict_filename = self.output_root_path + '/dictionary/dictionary.dict'

        self.corpus_filename = self.output_root_path + '/corpus/corpus.mm'
        self.tfidf_corpus_filename = self.output_root_path + '/corpus/tfidf.mm'

        self.lsi_filename = self.output_root_path + '/models/lsi.model'
        self.tfidf_model_filename = self.output_root_path + '/models/tfidf.model'

        self.lsi_index_filename = self.output_root_path + '/index/lsi_index'
        self.tfidf_idx_filename = self.output_root_path + '/index/tfidf.index'

        self.doc2id_filename = self.output_root_path + '/ids/word2id.pickle'
        self.id2doc_filename = self.output_root_path + '/ids/id2word.pickle'

        self.language = utils.getKeyFromSectionInConfiguration('bender-training', 'data_language_short', 'en',configDict)
        self.remove_stop_words = int(utils.getKeyFromSectionInConfiguration('bender-training', 'remove_stop_words', 1, configDict))
        self.stop_words = get_stop_words(self.language)
        self.brain = brain
        self._create_directories()

    def _create_directories(self):
        utils.safe_create_directory(self.output_root_path)
        utils.safe_create_directory(self.output_root_path + '/corpus')
        utils.safe_create_directory(self.output_root_path + '/models')
        utils.safe_create_directory(self.output_root_path + '/dictionary')
        utils.safe_create_directory(self.output_root_path + '/ids')
        utils.safe_create_directory(self.output_root_path + '/vectors')

    def _create_docs_dict(self):
        """
        Create the dictionaries that translate from document name to document index in the corpus, and viceversa
        """
        itemsInDict = self.brain.getDictionary().items()
        self.id2doc = dict(itemsInDict)
        reverseDict = {}
        for item in itemsInDict:
            reverseDict[item[1]] = item[0]
        self.doc2id = dict(reverseDict)

        max_id = int(max(self.id2doc.keys()))
        print('   | **** *******************************************************************')
        print('   | **** NOTE: Max WordID in vocabulary: --- %d ---' % max_id) 
        print('   | **** You will need that information for your Neuronal Network!!')
        print('   | **** --- iqa_eval.conf::main::n_words = %d' % (max_id + 2))
        print('   | **** *******************************************************************')
        print('   | Use %s as your vocabulary-file' % self.id2doc_filename)
        print('   | ........................................................................')
        pickle.dump(self.doc2id, open(self.doc2id_filename, "w"))
        pickle.dump(self.id2doc, open(self.id2doc_filename, "w"))

    def _generate_corpus(self):
        print("   | Generating original corpus from --BRAIN-- ...")
        self.corpus = TrainingCorpus(self.brain, self.brain.getDictionary(), self.remove_stop_words, self.stop_words)
        corpora.MmCorpus.serialize(self.corpus_filename, self.corpus)

    def _generate_tfidf_model(self):
        print('   | Generating Tfidf model...')
        self.tfidf = models.TfidfModel(self.corpus)
        self.tfidf.save(self.tfidf_model_filename)

    def _generate_lsi_model(self):
        print('   | Generating LSI model...');
        self.lsi = models.LsiModel(self.tfidf[self.corpus], id2word=self.brain.getDictionary(), num_topics=self.num_topics)
        self.lsi.save(self.lsi_filename)

    def _generate_word2vec(self):
        print('   | Generating Word2Vec model...')
        self.word2vec_filename = os.path.join(self.output_root_path, 'vectors', 'word2vec.embeddings')
        w2v_dim = 100
        w2v_mc = 5
        w2v_win = 5
        w2v_iter = 10
        w2v_workers = 4
        preserve_original_w2v = 0
        if self.config_dict is not None:
            w2v_dim = int(self.config_dict['bender-training'].get('word2vec_dims', w2v_dim))
            w2v_mc = int(self.config_dict['bender-training'].get('word2vec_min_count', w2v_mc))
            w2v_win = int(self.config_dict['bender-training'].get('word2vec_window', w2v_win))
            w2v_iter = int(self.config_dict['bender-training'].get('word2vec_iter', w2v_iter))
            w2v_workers = int(self.config_dict['bender-training'].get('word2vec_workers', w2v_workers))
            preserve_original_w2v = int(self.config_dict['bender-training'].get('preserve_original_w2vmodel', preserve_original_w2v))
        sentences = read_all_sentences(self.train_data_source_dir, self.remove_stop_words, self.stop_words)
        sentences += read_all_sentences(self.dict_source_dir, self.remove_stop_words, self.stop_words)
        print('   | ... starting word2vec generation ...')
        model = models.Word2Vec(sentences, size=w2v_dim, min_count=w2v_mc, iter=w2v_iter, window=w2v_win, workers=w2v_workers, sg=1)
        if preserve_original_w2v == 1:
            original_w2v_path = self.config_dict['bender-training'].get('original_w2v_path', None)
            original_w2v_filename = os.path.join(original_w2v_path, 'word2vec_orig.embeddings')
            model.save(original_w2v_filename)

        weights = model.wv.syn0
        d = dict([(k, v.index) for k, v in model.wv.vocab.items()])
        emb = numpy.zeros(shape=(len(self.doc2id)+1, w2v_dim), dtype='float32')
        for i, w in self.doc2id.items():
            if w not in d: continue
            emb[i, :] = weights[d[w], :]
        numpy.save(open(self.word2vec_filename, 'wb'), emb)
        print('   | ... done')

    def create(self, remove_stop_words=True):
        """
        Create all the necessary objects for the model. If any object does not exist, it will generate it.
        """
        if self.brain.getDictionary() == None:
            print('**** ERROR: GENSIMMODEL-GENERATOR -- You have to first set a dictionary.')
            sys.exit(1)

        print('   | *** Generating corpus, models & indices. This can take a while...')
        self._generate_corpus()
        # tfidf must be generated FIRST before generating LSI
        self._generate_tfidf_model()
        self._generate_lsi_model()
        self._create_docs_dict()
        self._generate_word2vec()
        print('   | *** ... done ...')
    
