# -*- coding: utf-8 -*-
from __future__ import print_function
import sys 
reload(sys)
sys.setdefaultencoding("utf-8")
"""
GenSimModel - incl. class GenSimModel and auxiliary classes & functions
Copyright (c) 2019 Imdat Solak
Copyright (c) 2014 Mohamed Sordo <mohamed.sordo@gmail.com>
                         http://msordo.weebly.com/
All rights reserved.

GenSimModel is partially based on "class model" from Mohamed Sordo, but significantly
altered and bug-fixed to adapt to multi-file reading/comparing.

TfIfd index & similarity code is (c) 2017 M-AILABS, written by Imdat Solak (ISO)
"""
import pickle
import numpy
from gensim import corpora, models, similarities, matutils
import gensim
from nltk.tokenize import RegexpTokenizer
from stop_words import get_stop_words
import nltk.data
from core import utils
import os as os
import re
import codecs
import itertools
from six import string_types
import logging
from core.gensim_utils import cosine
import threading
from modules.brain.mlbrain import MLBrain, TrainingCorpus
from multiprocessing import Lock, Process, Queue, current_process


MAX_DOCS = 10000000  # clip the dataset at this many docs, if larger (=use a wiki subset)

# Extract tokens from text
wordTokenizer = RegexpTokenizer(u'\w+')
sentenceTokenizer = nltk.data.load('tokenizers/punkt/english.pickle')

# Get a list of common english words that can be removed from tokens
en_stop = get_stop_words('de')
# Add additional words if neccessary to remove noisy information in SSD Config

lsi_mutex = threading.Lock()
lsi_add_mutex = threading.Lock()


def save_lsi_index_process_incremental(lsi, lsi_filename, documents, corpus, in_q, out_q):
    logger = logging.getLogger(os.path.basename(sys.argv[0]))
    logger.info('SaveLSIIndexProcess:: Create TfIdfModel for complete corpus')
    tfidf = gensim.models.TfidfModel(corpus)
    logger.info('SaveLSIIndexProcess:: Create TfIdfModel for new documents')
    tfidf_to_add = gensim.models.TfidfModel(documents)
    logger.info('SaveLSIIndexProcess:: Add new TfIdf to LSI')
    lsi.add_documents(tfidf_to_add[documents])
    logger.info('SaveLSIIndexProcess:: Save LSI')
    lsi.save(lsi_filename)
    logger.info('SaveLSIIndexProcess:: Generate LSI Index')
    lsi_index = gensim.similarities.MatrixSimilarity(lsi[corpus])
    logger.info('SaveLSIIndexProcess:: Send LSI, LSI_INDEX, TFIDF to PARENT')
    out_q.put(lsi)
    out_q.put(lsi_index)
    out_q.put(tfidf)
    out_q.close()
    logger.info('SaveLSIIndexProcess:: Wait for PARENT to confirm RECEIPT')
    done = in_q.get()
    logger.info('SaveLSIIndexProcess:: *** DONE *** ')
    os._exit(0)
    return True


def save_lsi_index_process(dictionary, num_topics, tfidf_filename, lsi_filename, corpus, in_q, out_q):
    logger = logging.getLogger(os.path.basename(sys.argv[0]))
    logger.info('SaveLSIIndexProcess:: Create TfIdfModel for complete corpus')
    tfidf = gensim.models.TfidfModel(corpus)
    logger.info('SaveLSIIndexProcess:: Save TfIdfModel ')
    tfidf.save(tfidf_filename)
    logger.info('SaveLSIIndexProcess:: Create new LSI')
    lsi = gensim.models.LsiModel(corpus, id2word=dictionary, num_topics=num_topics)
    logger.info('SaveLSIIndexProcess:: Save LSI')
    lsi.save(lsi_filename)
    logger.info('SaveLSIIndexProcess:: Generate LSI Index')
    lsi_index = gensim.similarities.MatrixSimilarity(lsi[corpus])
    logger.info('SaveLSIIndexProcess:: Send LSI, LSI_INDEX, TFIDF to PARENT')
    out_q.put(lsi)
    out_q.put(lsi_index)
    out_q.put(tfidf)
    out_q.close()
    logger.info('SaveLSIIndexProcess:: Wait for PARENT to confirm RECEIPT')
    done = in_q.get()
    logger.info('SaveLSIIndexProcess:: *** DONE *** ')
    os._exit(0)
    return True


def save_lsi_index_new(model, documents):
    logger = logging.getLogger(os.path.basename(sys.argv[0]))
    if model.getRequiresRetraining() == False:
        logger.info('LSI  : NO RETRAINING REQUIRED')
        model.retrainingDone()
        return

    model.setRequiresRetraining(False)
    try:
        lsi_mutex.acquire()
        logger.info('LSI  : RECREATING INDEX')
        lsi = model.lsi
        # Let's first create the UPDATED COMPLETE corpus and the TfIdf for it.
        # We need it for the next re-start of the application
        logger.info('SaveLSIIndex(PARENT): Create Training Corpus')
        corpus = TrainingCorpus(model.brain, model.brain.getDictionary(), model.remove_stop_words, model.stop_words)
        logger.info('SaveLSIIndex(PARENT): Save Corpus')
        gensim.corpora.MmCorpus.serialize(model.corpus_filename, corpus)

        logger.info('SaveLSIIndex(PARENT): Start CHILD Process')
        in_q = Queue()
        out_q = Queue()
        # process = Process(target=save_lsi_index_process_incremental, args=(lsi, model.lsi_filename, documents, corpus, in_q, out_q))
        process = Process(target=save_lsi_index_process, args=(model.brain.getDictionary(), model.num_topics, model.tfidf_model_filename, model.lsi_filename, corpus, in_q, out_q))
        process.start()
        logger.info('SaveLSIIndex(PARENT): WAIT for RESPONSE FROM CHILD')
        lsi = out_q.get()
        lsi_index = out_q.get()
        tfidf = out_q.get()
        logger.info('SaveLSIIndex(PARENT): RESPONSE RECEIVED')
        if lsi != None and lsi_index != None and tfidf != None:
            model.set_new_lsi_index(lsi, lsi_index, tfidf, corpus)
            logger.info('Successfully saved UPDATED LSI-Index...')
        else:
            logger.info('Error saving LSI-Index/retrieving data from Process...')
        lsi_mutex.release()
        in_q.put('THANKS')
        in_q.close()
        logger.info('SaveLSIIndex(PARENT): REMOVING CHILD FROM PROCESSES')
        process.join()
        logger.info('SaveLSIIndex(PARENT): CHILD REMOVED')
        model.retrainingDone()
    except:
        model.setRequiresRetraining(True)
        model.retrainingDone()


class GenSimModel:
    def __init__(self, brain, moduleConfig, configDict):
        self.logger = logging.getLogger(os.path.basename(sys.argv[0]))
        self.config_dict = configDict
        self.lsi_index_mutex = threading.Lock()
        self.module_config = moduleConfig
        self.num_topics = int(utils.getKeyFromSectionInConfiguration('bender-training', 'num_topics_lsi', 200, configDict))
        self.output_root_path = utils.getKeyFromSectionInConfiguration('bender-training', 'output_path', None, configDict)
        self.corpus_filename = self.output_root_path + '/corpus/corpus.mm'
        self.tfidf_corpus_filename = self.output_root_path + '/corpus/tfidf.mm'
        self.lsi_filename = self.output_root_path + '/models/lsi.model'
        self.tfidf_model_filename = self.output_root_path + '/models/tfidf.model'
        self.lsi_index_filename = self.output_root_path + '/index/lsi_index'
        self.tfidf_idx_filename = self.output_root_path + '/index/tfidf.index'
        self.doc2id_filename = self.output_root_path + '/ids/word2id.pickle'
        self.id2doc_filename = self.output_root_path + '/ids/id2word.pickle'
        self.word2vec_filename = os.path.join(self.output_root_path, 'vectors', 'word2vec.embeddings')
        self.language = utils.getKeyFromSectionInConfiguration('bender-training', 'data_language_short', 'en',configDict)
        self.remove_stop_words = int(utils.getKeyFromSectionInConfiguration('bender-training', 'remove_stop_words', 1, configDict))
        self.stop_words = get_stop_words(self.language)
        self.brain = brain
        retraining_interval_mins = int(self.module_config.get('retraining_interval_in_minutes', 3))
        if retraining_interval_mins < 3:
            retraining_interval_mins = 3
        self.retraining_interval_in_seconds = retraining_interval_mins * 60
        self.learning_update_timer = None
        self.learning_lock = threading.Lock()
        self.requires_learning = False
        self._load()

    def _load(self):
        self.logger.info('   | *** Loading corpus, models & indices. This can take a while...')
        self.logger.info("   | Loading corpus... ")
        self.corpus = corpora.MmCorpus(self.corpus_filename)
        self.logger.info('done')
        self.logger.info('   | Loading Tfidf model... ')
        self.tfidf = models.TfidfModel.load(self.tfidf_model_filename)
        self.logger.info('done')
        self.logger.info('   | Loading LSI model... ')
        self.lsi = models.LsiModel.load(self.lsi_filename)
        #self.lsi_index = similarities.Similarity.load(self.lsi_index_filename)
        self.lsi_index = similarities.MatrixSimilarity(self.lsi[self.corpus])
        self.doc2id = pickle.load(open(self.doc2id_filename))
        self.id2doc = pickle.load(open(self.id2doc_filename))
        self.logger.info('done')
        self.learning_update_timer = None
        self.resetLearningTimer()

    def get_corpus(self):
        return self.corpus

    def _get_qids_similar_to_text_tfidf(self, text, num_sim):
        global wordTokenizer
        tokens = wordTokenizer.tokenize(text.lower())
        test_corpus = self.brain.getDictionary().doc2bow(tokens)
        if test_corpus:
            test_corpus_tfidf = self.tfidf[test_corpus]
            sims = self.tfidf_index[test_corpus_tfidf]
            sims = sorted(enumerate(sims), key=lambda item: -item[1])[:num_sim]
            return sims[:min(len(sims), num_sim)]
        else:
            return None

    def _get_qids_similar_to_text_lsi(self, text, num_sim):
        tokens = wordTokenizer.tokenize(text.lower())
        text_bow = self.brain.getDictionary().doc2bow(tokens)
        if text_bow:
            # If we have a problem with multi-threading because of the 'set_new_lsi_index' method below
            # we should introduce a mutex-lock and try acquiring it here:
            # self.lsi_index_mutex.acquire() and release it immediately after the following
            # line of code...
            # self.lsi_index_mutex.acquire()
            sims = self.lsi_index[self.lsi[self.tfidf[text_bow]]]
            # self.lsi_index_mutex.release()
            sims = sorted(enumerate(sims), key=lambda item: -item[1])
            return sims[:min(len(sims), num_sim)]
        else:
            return None
   
    def get_text_similarity(self, text, num_sim, method='tfidf'):
        if method == 'tfidf':
            return self._get_qids_similar_to_text_tfidf(text, num_sim)
        elif method == 'lsi':
            return self._get_qids_similar_to_text_lsi(text, num_sim)
        else:
            return None

    def add_new_entry(self, text):
        try:
            tokens = wordTokenizer.tokenize(text.lower())
            text_bow = self.brain.getDictionary().doc2bow(tokens)
            if text_bow:
                self.lsi.add_documents([self.tfidf[text_bow]])
                self.lsi_index = similarities.MatrixSimilarity(self.lsi[self.corpus])
                return True
            else:
                return False
        except:
            return False

    def set_new_lsi_index(self, new_lsi, new_lsi_index, new_tfidf, new_corpus):
        # This method is called from a separate thread. This *can* cause a problem if, during this call,
        # we are asked to do a similarity analysis for a moment. But this shouldn't be much of a problem.
        # Even though these are just "pointer assignments", we don't want to end up using
        # a new "lsi" with an old "corpus" somewhere else. This is just for security purposes
        # This lock/release is fast enough that it should not have any impact on the overall performance..
        self.lsi_index_mutex.acquire()
        self.lsi = new_lsi
        self.lsi_index = new_lsi_index
        self.tfidf = new_tfidf
        self.corpus = new_corpus
        self.lsi_index_mutex.release()

    def compare_texts(self, text1, text2):
        return 0.0

    def setRequiresRetraining(self, flag):
        self.learning_lock.acquire()
        self.requires_learning = flag
        self.learning_lock.release()

    def getRequiresRetraining(self):
        return self.requires_learning

    def resetLearningTimer(self):
        # Every <interval> time, we check whether we need to update the LSI-Index. If so, we do 
        # it in a separate process...
        if self.learning_update_timer != None:
            return
        self.learning_update_timer = threading.Timer(self.retraining_interval_in_seconds, save_lsi_index_new, args=(self, None))
        self.learning_update_timer.start()

    def retrainingDone(self):
        # re-schedules re-training
        self.learning_update_timer = threading.Timer(self.retraining_interval_in_seconds, save_lsi_index_new, args=(self, None))
        self.learning_update_timer.start()

