# -*- coding: utf-8 -*-
from __future__ import print_function
import sys 
reload(sys)
sys.setdefaultencoding("utf-8")

import os
import logging
import requests
import json
from stop_words import get_stop_words
import nltk.data
from nltk.tokenize import RegexpTokenizer
import gensim
import shutil
import codecs
from gensim import models, corpora, similarities, matutils
from gensim.similarities import WmdSimilarity
from core import utils
import threading
from modules.machinelogic.imachinelogic.mlimachinelogic import MLInternalMachineLogic, MLInternalMachineLogicTrainer
from modules.brain.mlbrain import MLBrain, TrainingCorpus, convert_train_data
from core.progressbar import ProgressBar, Percentage, Bar, ETA, FormatLabel, AnimatedMarker
from time import sleep
from multiprocessing import Lock, Process, Queue, current_process

wordTokenizer = RegexpTokenizer(u'\w+')
"""
Class MLInternalMachineLogic as described at:

Copyright (c) 2019 Imdat Solak
            All Rights Reserved
"""
WMD_FILE = 'wmd.emb'
wmd_mutex = threading.Lock()
query_results_mutex = threading.Lock()

# Extract tokens from text
sentenceTokenizer = nltk.data.load('tokenizers/punkt/english.pickle')

# Get a list of common German words that can be removed from tokens
en_stop = get_stop_words('en')
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
                    pass
        pBar.finish()
    return sentences


def perform_query_for_job_on_instance_process(wmd_logic, wmd_instances, query, jobID, instance, in_q, out_q):
    sims = []
    logger = logging.getLogger(os.path.basename(sys.argv[0]))
    if len(query):
        logger.info('WMD: Searching at instance {}'.format(instance))
        wmd_instance = wmd_instances[instance]
        sims = wmd_instance[query]
    
    logger.info('WMD: Sending result from instance {} to parent'.format(instance))
    out_q.put(sims)
    out_q.close()
    logger.info('WMD: Waiting for RECEIPT from parent at instance {}'.format(instance))
    done = in_q.get()
    os._exit(0)


def create_wmd_instances_process(all_knowledge, wmd_model, num_results, wmd_instance_count, in_q, out_q):
    """
    This function updates the WMD-Instance used in the WMDLogicModule
    NOTE: This runs in a its own processes in order not to block
    return answers faster...
    """
    logger = logging.getLogger(os.path.basename(sys.argv[0]))
    logger.info('   |    +----> CHILD: RE-Creating in separate process...')
    sys.stdout.flush()
    wmd_instances = []
    wmd_corpus = []
    for tokens in all_knowledge:
        wmd_corpus.append(tokens)

    if wmd_instance_count > len(wmd_corpus):
        wmd_instance_count = len(wmd_corpus)
    chunk_size = int(len(wmd_corpus) / wmd_instance_count)
    for i in range(0, wmd_instance_count):
        logger.info(' Instance %d..' %i)
        sys.stdout.flush()
        if i == wmd_instance_count -1:
            wmd_instance = WmdSimilarity(wmd_corpus[i*chunk_size:], wmd_model, num_results)
        else:
            wmd_instance = WmdSimilarity(wmd_corpus[i*chunk_size:(i+1)*chunk_size], wmd_model, num_results)
        wmd_instances.append(wmd_instance)
    logger.info('   |    +----> CHILD: Adding chunksize to out_q')
    out_q.put(chunk_size)
    logger.info('   |    +----> CHILD: Adding instances to out_q')
    out_q.put(wmd_instances)
    out_q.close()
    logger.info('   |    +----> CHILD: Waiting for data to be flushed to my PARENT...')
    done = in_q.get()
    logger.info('   |    +----> CHILD: I have done my job (Parent is happy), I am going away now...')
    os._exit(0)
    return True


def recreate_wmd_instances(wmd_logic_module, wmd_model, brain, num_results, wmd_instance_count):
    """
    This function updates the WMD-Instance used in the WMDLogicModule
    NOTE: This runs in a its own thread in order not to block
    return answers faster...
    """
    logger = logging.getLogger(os.path.basename(sys.argv[0]))
    if wmd_logic_module.getRequiresRetraining() == False:
        logger.info('WMD  : NO RETRAINING REQUIRED')
        wmd_logic_module.retrainingDone()
        return

    wmd_logic_module.setRequiresRetraining(False)
    try:
        wmd_mutex.acquire()
        logger.info('WMD  : RECREATING INDEX')
        wmd_instances = []
        wmd_corpus = []
        corpus_data = brain.getAllQuestions()
        for q in corpus_data:
            t = ' '.join(q.strip().lower().split('\n'))
            t = brain.getStopWordCleanedText(t)
            tokens = wordTokenizer.tokenize(t)
            wmd_corpus.append(tokens)

        out_q = Queue()
        in_q = Queue()
        process = Process(target=create_wmd_instances_process, args=(wmd_corpus, wmd_model, num_results, wmd_instance_count, in_q, out_q))
        process.start()
        logger.info('   | +--> Waiting for response from my child...')
        chunk_size = out_q.get()
        wmd_instances = out_q.get()
        logger.info('   | +--> Retrieved data from CHILD, great kid. I will let it know everything was fine...')
        if isinstance(chunk_size, int) and isinstance(wmd_instances, list):
            wmd_logic_module.setWMDInstances(wmd_instances, chunk_size)
            wmd_mutex.release()
        else:
            logger.info('   | *** ERROR: Queue was corrupted...')
            wmd_mutex.release()
        in_q.put('DONE')
        in_q.close()
        process.join()
        wmd_logic_module.retrainingDone()
    except:
        wmd_logic_module.setRequiresRetraining(True)
        wmd_logic_module.retrainingDone()


class WMDLogicMTTrainer(MLInternalMachineLogicTrainer):
    def __init__(self, moduleConfigSection, configDict, brain):
        super(WMDLogicMTTrainer, self).__init__(moduleConfigSection, configDict, brain)
        self.brain = brain
        if moduleConfigSection != None:
            self.module_config = moduleConfigSection
        else:
            print('**** ERROR: moduleConfigSection cannot be None!')
            sys.exit(1)
        self.config_dict = configDict

    def _generate_word2vec(self):
        global WMD_FILE
        print('   | Generating Word2Vec model...')
        wmd_data_path = self.module_config.get('wmd_data_path', None)
        if wmd_data_path == None:
            logger.info('**** Error: no output_root_path specified in section my i-machinelogic-section in the config-file.')
            sys.exit(1)
        else:
            utils.safe_create_directory(wmd_data_path)

        w2v_dim = 100
        w2v_mc = 5
        w2v_win = 5
        w2v_iter = 10
        w2v_workers = 4
        create_nn_embed = 0
        nn_embed_path = None
        if self.config_dict is not None:
            w2v_dim = int(self.config_dict['bender-training'].get('word2vec_dims', w2v_dim))
            w2v_mc = int(self.config_dict['bender-training'].get('word2vec_min_count', w2v_mc))
            w2v_win = int(self.config_dict['bender-training'].get('word2vec_window', w2v_win))
            w2v_iter = int(self.config_dict['bender-training'].get('word2vec_iter', w2v_iter))
            w2v_workers = int(self.config_dict['bender-training'].get('word2vec_workers', w2v_workers))
            create_nn_embed = int(self.config_dict['bender-training'].get('create_nn_embed', 0))
            nn_embed_path = self.config_dict['bender-training'].get('nn_embed_path', None)
            train_data_source_dir = self.config_dict['bender-training'].get('train_data_source_file', None)
            remove_stop_words = int(self.config_dict['bender-training'].get('remove_stop_words', 0))
            language = self.config_dict['bender-training'].get('data_language_short', 'en')
            stop_words = get_stop_words(language)
            if train_data_source_dir is not None:
                train_data_source_dir = os.path.dirname(train_data_source_dir)
            dict_source_dir = self.config_dict['bender-training'].get('dictionary_data_source_path')
        else:
            print('Error: SOMETHING IS REALLY BAD HERE. No CONFIG-FILE FOUND')
            sys.exit(1)
        if train_data_source_dir is not None:
            sentences = read_all_sentences(train_data_source_dir, remove_stop_words, stop_words)
        else:
            sentences = []
        sentences += read_all_sentences(dict_source_dir, remove_stop_words, stop_words)
        print('   | ... starting word2vec generation ...')
        model = models.Word2Vec(sentences, size=w2v_dim, min_count=w2v_mc, iter=w2v_iter, window=w2v_win, workers=w2v_workers, sg=1)
        wmd_w2v_filename = os.path.join(wmd_data_path, WMD_FILE)
        model.save(wmd_w2v_filename)
        if create_nn_embed == 1 and nn_embed_path is not None:
            weights = model.wv.syn0
            d = dict([(k, v.index) for k, v in model.wv.vocab.items()])
            emb = numpy.zeros(shape=(len(self.doc2id)+1, w2v_dim), dtype='float32')
            for i, w in self.doc2id.items():
                if w not in d: continue
                emb[i, :] = weights[d[w], :]
            numpy.save(open(os.path.join(nn_embed_path, 'word2vec_nn.embed'), 'wb'), emb)
        print('   | ... done')

    def train(self):
        self._generate_word2vec()

    def reTrain(self):
        # self._generate_word2vec()
        return None


class WMDLogicMT(MLInternalMachineLogic):
    def __init__(self, moduleConfigSection, configDictionary):
        super(WMDLogicMT, self).__init__(moduleConfigSection, configDictionary)
        global WMD_FILE
        self.profile = {
                        "name" : "wmd-logic",
                        "class" : "internalmachine-logic",
                        'accepted-languages': ['de','en','fr','tr','it','nl','se','no','fi','pl','cz','hu'],
                        'accepted-media-types' : ['text/utf8'],
                        'returned-media-types' : ['text/utf8'],
                        'requires-original-query' : True,
                        'returns-response-id' : True,
                        'always-ask' : True
                        }
        self.module_config = moduleConfigSection
        self.config_dict = configDictionary
        language = utils.getKeyFromSectionInConfiguration('bender-training', 'data_language_short', 'en', self.config_dict)
        self.remove_stop_words = int(utils.getKeyFromSectionInConfiguration('bender-training', 'remove_stop_words', 1, self.config_dict))        
        retraining_interval_mins = int(self.module_config.get('retraining_interval_in_minutes', 23))
        if retraining_interval_mins < 5:
            retraining_interval_mins = 5
        self.retraining_interval_in_seconds = retraining_interval_mins * 60
	self.stop_words = get_stop_words(language)
        self.higher_threshold = float(self.module_config.get('wmd_higher_threshold', 0.7))
        self.lower_threshold = float(self.module_config.get('wmd_lower_threshold', 0.5))
        self.num_results = int(self.module_config.get('max_wmd_results', '10'))
        self.num_instances = int(self.module_config.get('wmd_num_instances', '10'))
        self.wmd_timeout = int(self.module_config.get('wmd_timeout', '30'))
        self.logger = logging.getLogger(os.path.basename(sys.argv[0]))
        self.is_master = int(self.module_config.get('is-master', 0))
        self.contribution_factor = int(self.module_config.get('contribution-factor', 500))
        self.wmd_model = None
        self.wmd_instances = []
        self.query_results = {}
        self.process_queues = {}
        self.chunk_size = 0
        self.learning_update_timer = None
        self.learning_lock = threading.Lock()
        self.requires_learning = False
        self.wmd_instances_lock = threading.Lock()

    def capabilities(self):
        return self.profile

    def isMaster(self):
        return self.is_master

    def contributionFactor(self):
        return self.contributionFactor
  
    def _updateWMD(self):
        if self.wmd_model == None:
            self.logger.info('   | +--> Loading WMD W2V data... ')
            sys.stdout.flush()
            wmd_data_path = self.module_config.get('wmd_data_path', None)
            wmd_filename = os.path.join(wmd_data_path, WMD_FILE)
            self.wmd_model = models.Word2Vec.load(wmd_filename)
            self.logger.info('done')
            self.logger.info('   | +--> Initializing sims... ')
            sys.stdout.flush()
            self.wmd_model.init_sims(replace=True)
            self.logger.info('done')
        self.logger.info('   | +--> Generating %d WMD-Instances... ' % self.num_instances)
        sys.stdout.flush()
        self.setRequiresRetraining(True)
        self.learning_update_timer = None
        recreate_wmd_instances(self, self.wmd_model, self.brain, self.num_results, self.num_instances)
        self.logger.info('   | WMD is ready to be used... ')

    def setWMDInstances(self, new_wmd_instances, chunk_size):
        self.wmd_instances_lock.acquire()
        self.wmd_instances = new_wmd_instances
        self.chunk_size = chunk_size
        self.wmd_instances_lock.release()

    def initForBender(self, benderInstance, jobID=None):
        self.logger.info('   | Loading WMD i-machine model... ')
        sys.stdout.flush()
        self.benderCore = benderInstance
        self.brain = self.benderCore.getBrain()
        self._updateWMD()

    def _performTextQuerySimpleMT(self, query_doc, jobID):
        # This is tricky.........
        # Let's first initialize all potential instance-results with an empty array in order to 
        # 'allocate' the space
        # NOTE: As we are using the same code and memory-space for all Job-Processes,
        #       we need to know which job the result belongs to when a Processes sends us
        #       a result back... This is really tricky...
        self.logger.info('WMD: Will perform MT query')
        query_results_mutex.acquire()
        search_processes = []
        # Lock the wmd_instances as we need them as they are to start
        # our processes. Once the processes are started, they should have a 
        # copy of our wmd_instances, so we can release the lock then
        self.wmd_instances_lock.acquire()
        self.query_results[jobID] = []
        self.process_queues[jobID] = []
        for instance in range(0, self.num_instances):
            self.query_results[jobID].append([])
            in_q = Queue()
            out_q = Queue()
            self.process_queues[jobID].append([in_q, out_q])
            search_process = Process(target=perform_query_for_job_on_instance_process, args=(self, self.wmd_instances, query_doc, jobID, instance, in_q, out_q))
            search_processes.append(search_process)

        for i, sp in enumerate(search_processes):
            self.logger.info('WMD: launching porocess %d' % i)
            sp.start()
            self.logger.info('WMD: LAUNCHEND PROCESS %d' % i)

        # The processes should now have copies of our wmd_instances, so we can release
        # this lock...
        self.wmd_instances_lock.release()
        # After starting the processes, let's wait for their return
        # This happens by waiting for the "OUT_Q" having the data we need (OUT from the processes perspective)
        # Once we receive our result, we send the process in its IN_Q a message that all is well.
        # Then we can join the process to finish it.
        # This is something we need to do for each process...
        for i, process in enumerate(search_processes):
            self.logger.info('WMD: waiting for child %d' % i)
            queues = self.process_queues[jobID][i]
            in_q = queues[0]
            out_q = queues[1]
            # Here, we might need a timeout in order not to wait forever...
            sims = out_q.get()
            # Send our child that we have received its information
            in_q.put('THANKS')
            # Close the comms-queue
            in_q.close()
            # Finish the process
            process.join()
            if sims != None and len(sims)>0:
                res = []
                # We need to scale the found ids back to our complete corpus size
                # since the indices we received are relative to each corpus...
                for sim in sims:
                    aSim = (int(sim[0] + (i * self.chunk_size)), sim[1])
                    res.append(aSim)

                if sims != None:
                    self.query_results[jobID][i] = res
        qResults = []
        if jobID in self.query_results.keys():
            qResults.extend(self.query_results[jobID])
            del self.query_results[jobID]
        if jobID in self.process_queues.keys():
            del self.process_queues[jobID]
        query_results_mutex.release()
        sims = []
        for r in qResults:
            sims.extend(r)
        if len(sims):
            return sims
        else:
            return None

    def _performTextQuerySimple(self, theQuery, num_results=10, jobID=None):
        global wordTokenizer
        higherThresholdExists = False
        query = ' '.join(theQuery.strip().lower().split('\n'))
        tokens = wordTokenizer.tokenize(query)
        if self.remove_stop_words:
            tokens = [w for w in tokens if not w in self.stop_words]
        query_doc = [w for w in tokens if w.isalpha()]
        sims = self._performTextQuerySimpleMT(query_doc, jobID)
        result = []
        if sims != None:
            sims = sorted(sims, key=lambda item: -item[1])
            sims = sims[:min(len(sims), num_results)]
            for sim in sims:
                if sim[1] > self.lower_threshold:
                    result.append({'response': sim[0], 'confidenceLevel':sim[1], 'responseIsID': True})
                    if sim[1] > self.higher_threshold:
                        higherThresholdExists = True
            if len(result) > 0:
                return result, higherThresholdExists
            else:
                return None, False
        else:
            return None, None
  
    def performTextQuery(self, originalQuery, num_results=10, jobID=None):
        retArr = []
        result, higherThresholdFound = self._performTextQuerySimple(originalQuery, num_results, jobID)
        if result != None:
            jcHC = self.benderCore.higherConfidenceLevel()
            jcLC = self.benderCore.lowerConfidenceLevel()
            for sim in result:
                similarityValue = float(sim['confidenceLevel'])
                # We need to normalize them for BenderCore thresholds
                # Otherwise BenderCore will either reject or ask a Human
                self.logger.info('.......... index=%s, sim=%f' % (str(sim['response']), similarityValue))
                if similarityValue >= self.lower_threshold:
                    if similarityValue >= self.higher_threshold:
                        multiplier = (1-jcHC) / (1-self.higher_threshold)
                        diff = similarityValue - self.higher_threshold
                        similarityValue = jcHC + (diff * multiplier)
                    else:
                        multiplier = (jcHC - jcLC) / (self.higher_threshold - self.lower_threshold)
                        diff = similarityValue - self.lower_threshold
                        similarityValue = jcLC + (diff * multiplier)
                    sim['confidenceLevel'] = similarityValue
                    self.logger.info('.......... -> index=%s, sim=%f' % (str(sim['response']), similarityValue))
                    sim['is-master'] = self.is_master
                    sim['contribution-factor'] = self.contribution_factor
                    retArr.append(sim)
        return retArr
  
    def performImageQuery(self, query):
        return None, None
  
    def performAudioQuery(self, query):
        return None, None
  
    def performVideoQuery(self, query):
        return None, None
  
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
        # Once we have created all WMD instance, we should fire of a timer that, every <interval> seconds
        # checks whether new learning is required. If so, it should update learning
        if self.learning_update_timer != None:
            return
        self.learning_update_timer = threading.Timer(self.retraining_interval_in_seconds, recreate_wmd_instances, args=(self, self.wmd_model, self.brain, self.num_results, self.num_instances))
        self.learning_update_timer.start()

    def retrainingDone(self):
        # Re-schedules re-training
        self.learning_update_timer = threading.Timer(self.retraining_interval_in_seconds, recreate_wmd_instances, args=(self, self.wmd_model, self.brain, self.num_results, self.num_instances))
        self.learning_update_timer.start()

