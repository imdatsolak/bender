# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
"""
Annoy Trainer
This is the implementation of Annoy, developed by Spotify.
The source code of Annoy Library and documentation about it can be found
at: 
    https://github.com/spotify/annoy

Copyright (c) 2019 Imdat Solak
Written: 2017-08-08 08:25, ISO

This part of the implementation generates the index used in doing similarity analysis
in the annoysim.py file.

This trainer may be called every <n> minutes...
The beauty of Annoy is that we can used shared indexes, i.e., we can generate the index
and save it to disk to be re-used by other classes.

This implementation is partly based on work done by Radim Rehurek (developer of Gensim)
to be found at:
    https://rare-technologies.com/performance-shootout-of-nearest-neighbours-contestants/

Updated: 2017-08-10 12:00 CET, ISO
         - Fixed a few bugs

"""

import os
import sys
import time
import logging
import itertools
from functools import wraps
import codecs

import numpy
from six import string_types
import gensim

import pickle
import json
import random
import bz2
import annoy
import shutil
import threading
from time import sleep
from multiprocessing import Lock, Process, Queue, current_process
from core.gensim_utils import cosine
from core import utils
from modules.brain.mlbrain import MLBrain, TrainingCorpus, convert_train_data
from modules.machinelogic.imachinelogic.mlimachinelogic import MLInternalMachineLogicTrainer, MLInternalMachineLogic

MAX_DOCS = 10000000  # clip the dataset at this many docs, if larger; should be enough for our customers 
LSI_VECTORS_FNAME = 'annoy.lsi.mm'
LSI_MODEL_FNAME = 'annoy.lsi.model'
TFIDF_MODEL_FNAME = 'annoy.tfidf.model'
ANNOY_OUTPUT_FNAME = 'annoy.idx'
CLIPPED_CORPUS_FNAME = 'clipped.npy'
annoy_mutex = threading.Lock()

def create_annoy_index(moduleConfigSection, configDict, dictionary, corpus, in_q, out_q):
    logger = logging.getLogger(os.path.basename(sys.argv[0]))
    module_config = moduleConfigSection
    config_dict = configDict
    num_topics_lsi = int(utils.getKeyFromSectionInConfiguration('bender-training', 'num_topics_lsi', 200, configDict))
    output_path = module_config.get('annoy_data_path', '')
    accuracy = int(module_config.get('accuracy', 500))
    max_results = int(module_config.get('max_results', 100))
    utils.safe_create_directory(output_path)
    lsi_vectors_file = os.path.join(output_path, LSI_VECTORS_FNAME)
    lsi_model_filename = os.path.join(output_path, LSI_MODEL_FNAME)
    tfidf_vectors_file = os.path.join(output_path, TFIDF_MODEL_FNAME)
    annoy_output_filename = os.path.join(output_path, ANNOY_OUTPUT_FNAME)
    clipped_output_filename = os.path.join(output_path, CLIPPED_CORPUS_FNAME)

    tfidf = gensim.models.TfidfModel(corpus)
    logger.info('Saving Tfidf...')
    tfidf.save(tfidf_vectors_file)

    logger.info('*** START generating LSI...')
    lsi = gensim.models.LsiModel(tfidf[corpus], id2word=dictionary, num_topics=num_topics_lsi)
    logger.info('*** DONE generating LSI...')
    lsi.save(lsi_model_filename)
    logger.info('*** SAVED generating LSI...')
    # convert all articles to latent semantic space, store the result as a MatrixMarket file
    # normalize all vectors to unit length, to simulate cossim in libraries that only support euclidean distance
    gensim.corpora.MmCorpus.serialize(lsi_vectors_file, (gensim.matutils.unitvec(vec) for vec in lsi[tfidf[corpus]]))
    mm = gensim.corpora.MmCorpus(lsi_vectors_file)
    num_features, num_docs = mm.num_terms, min(mm.num_docs, MAX_DOCS)
    clipped = numpy.empty((num_docs, num_features), dtype=numpy.float32)
    for docno, doc in enumerate(itertools.islice(mm, num_docs)):
        clipped[docno] = gensim.matutils.sparse2full(doc, num_features)

    logger.info('*** Saving clipped corpus as NUMPY...')
    numpy.save(clipped_output_filename, clipped)

    logger.info('*** Generating ANNOY...')
    clipped_corpus = gensim.matutils.Dense2Corpus(clipped, documents_columns=False)
    index_annoy = annoy.AnnoyIndex(num_features, metric='angular')
    for i, vec in enumerate(clipped_corpus):
        index_annoy.add_item(i, list(gensim.matutils.sparse2full(vec, num_features).astype(float)))
    logger.info('*** Building ANNOY...')
    index_annoy.build(accuracy)
    logger.info('*** Saving ANNOY...')
    index_annoy.save(annoy_output_filename)

    out_q.put('DONE')
    out_q.close()
    done = in_q.get()
    os._exit(0)
    return True


def recreate_annoy_index(moduleConfigSection, configDict, brain, annoy_logic_module = None):
    """
    This function updates the Annoy Index in multi-threaded mode. It is also used 
    in single-threaded mode for the initial training.
    NOTE: This runs in a its own thread in order not to block
    return answers faster...
    """
    logger = logging.getLogger(os.path.basename(sys.argv[0]))
    if annoy_logic_module != None and annoy_logic_module.getRequiresRetraining() == False:
        logger.info('ANNOY: NO RETRAINING REQUIRED')
        annoy_logic_module.retrainingDone()
        return

    if annoy_logic_module != None:
        annoy_logic_module.setRequiresRetraining(False)
    try:
        logger.info('ANNOY: STARTING RECREATING THE INDEX...')
        annoy_mutex.acquire()
        out_q = Queue()
        in_q = Queue()
        dictionary = brain.getDictionary()
        corpus = TrainingCorpus(brain, dictionary, False, None)
        process = Process(target=create_annoy_index, args=(moduleConfigSection, configDict, dictionary, corpus, in_q, out_q))
        process.start()

        logger.info('   | +--> Waiting for response from my child...')
        done = out_q.get()
        logger.info('   | +--> Retrieved data from CHILD, great kid. I will let it know everything was fine...')
        in_q.put('DONE')
        in_q.close()
        process.join()
        if annoy_logic_module != None:
            annoy_logic_module.retrainingDone()
        annoy_mutex.release(())
    except:
        if annoy_logic_module != None:
            annoy_logic_module.setRequiresRetraining(True)
            annoy_logic_module.retrainingDone()

        
class AnnoySimTrainer(MLInternalMachineLogicTrainer):
    def __init__(self, moduleConfigSection, configDict, brain):
        super(AnnoySimTrainer, self).__init__(moduleConfigSection, configDict, brain)
        if moduleConfigSection != None:
            self.module_config = moduleConfigSection
        else:
            print('**** ERROR: moduleCOnfigSection cannot be None!')
            sys.exit(1)
        self.brain = brain
        self.configDict = configDict


    def train(self):
        recreate_annoy_index(self.module_config, self.configDict, self.brain)


    def reTrain(self):
        recreate_annoy_index(self.module_config, self.configDict, self.brain)


class AnnoySim(MLInternalMachineLogic):
    def __init__(self, moduleConfigSection, configDictionary):
        super(AnnoySim, self).__init__(moduleConfigSection, configDictionary)
        self.profile = {
                        "name" : "annoy-logic",
                        "class" : "internalmachine-logic",
                        'accepted-languages': ['de','en','fr','tr','it','nl','se','no','fi','pl','cz','hu'],
                        'accepted-media-types' : ['text/utf8'],
                        'returned-media-types' : ['text/utf8'],
                        'requires-original-query' : True,
                        'returns-response-id' : True
                }
	self.module_config = moduleConfigSection
        self.config_dict = configDictionary
        self.learning_update_timer = None
        self.is_master = int(self.module_config.get('is-master', 0))
        self.contribution_factor = int(self.module_config.get('contribution-factor', 500))
        self.requires_learning = False
        self.loading_lock = threading.Lock()
        self.learning_lock = threading.Lock()
        self.logger = logging.getLogger(os.path.basename(sys.argv[0]))

    def capabilities(self):
        return self.profile

    def initForBender(self, benderInstance, jobID = None):
        self.benderCore = benderInstance
        self.brain = self.benderCore.getBrain()
        self.logger.info('ANNOY: Loading index...')
        self._loadAnnoyIndex()
        self.resetLearningTimer()

    def isMaster(self):
        return self.is_master

    def contributionFactor(self):
        return self.contribution_factor

    def _loadAnnoyIndex(self):
        self.loading_lock.acquire()
        self.dictionary = self.brain.getDictionary()
        self.num_topics_lsi = int(utils.getKeyFromSectionInConfiguration('bender-training', 'num_topics_lsi', 200, self.config_dict))
        self.output_path = self.module_config.get('annoy_data_path', '')
        self.accuracy = int(self.module_config.get('accuracy', 500))
        self.max_results = int(self.module_config.get('max_results', 100))
        retraining_iv = int(self.module_config.get('retraining_interval_in_minutes', 7))
        self.retraining_interval_in_seconds = retraining_iv * 60
        utils.safe_create_directory(self.output_path)
        self.lsi_vectors_filename = os.path.join(self.output_path, LSI_VECTORS_FNAME)
        self.lsi_model_filename = os.path.join(self.output_path, LSI_MODEL_FNAME)
        self.tfidf_model_filename = os.path.join(self.output_path, TFIDF_MODEL_FNAME)
        self.annoy_index_filename = os.path.join(self.output_path, ANNOY_OUTPUT_FNAME)
        self.clipped_corpus_filename = os.path.join(self.output_path, CLIPPED_CORPUS_FNAME)
        if os.path.exists(self.annoy_index_filename):
            self.mm = gensim.corpora.MmCorpus(self.lsi_vectors_filename)
            num_features, num_docs = self.mm.num_terms, min(self.mm.num_docs, MAX_DOCS)
            self.index_annoy = annoy.AnnoyIndex(num_features, metric='angular')
            self.index_annoy.load(self.annoy_index_filename)
        else:
            print('**** ERROR: Annoy index does not exist. Please train first!')
            sys.exit(1)

        if os.path.exists(self.lsi_model_filename):
            self.lsi_model = gensim.models.LsiModel.load(self.lsi_model_filename)
        else:
            print('**** ERROR: Annoy LSI Model missing. Please train first!')
            sys.exit(1)

        if os.path.exists(self.tfidf_model_filename):
            self.tfidf_model = gensim.models.TfidfModel.load(self.tfidf_model_filename)
        self.loading_lock.release()

    def performTextQuery(self, originalQuery, num_results=None, jobID=None):
        if num_results == None:
            num_results = self.max_results
        tokens = originalQuery.lower().split()
        d2b = self.dictionary.doc2bow(tokens)
        clipped = numpy.empty((1, self.num_topics_lsi), dtype=numpy.float32)
        vec = gensim.matutils.unitvec(self.lsi_model[self.tfidf_model[d2b]])
        if len(vec) < self.num_topics_lsi:
            return None

        clipped[0] = gensim.matutils.sparse2full(vec, len(vec))
        queries = clipped
        result = self.index_annoy.get_nns_by_vector(list(queries[0].astype(float)), num_results)
        return_res = []
        for i, r in enumerate(result):
            found_entry = {'response': r, 'confidenceLevel': 0.0, 'responseIsID': True, 'is-master': self.is_master, 'contribution-factor': self.contribution_factor}
            return_res.append(found_entry)
        return return_res

    def reinforceCorrectResponse(self, query, response, inputMediaType, outputMediaType):
        self.setRequiresRetraining(True)
        self.resetLearningTimer()
        return None, None
    
    def reinforceWrongResponse(self, query, response, inputMediaType, outputMediaType):
        self.setRequiresRetraining(True)
        self.resetLearningTimer()
        return None, None

    def setRequiresRetraining(self, flag):
        self.learning_lock.acquire()
        self.requires_learning = flag
        self.learning_lock.release()

    
    def getRequiresRetraining(self):
        return self.requires_learning

    def resetLearningTimer(self):
        if self.learning_update_timer != None:
            return
        self.learning_update_timer = threading.Timer(self.retraining_interval_in_seconds, recreate_annoy_index, args=(self.module_config, self.config_dict, self.brain, self))
        self.learning_update_timer.start()

    def retrainingDone(self):
        self._loadAnnoyIndex()
        self.learning_update_timer = None
        self.resetLearningTimer()

