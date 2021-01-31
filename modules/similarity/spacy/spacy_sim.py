# -*- coding: utf-8 -*-
from __future__ import print_function
import sys 
reload(sys)
sys.setdefaultencoding("utf-8")
import logging
import spacy
import threading
import os
from core import utils
from modules.similarity.mlsimilarity import MLSimilarity
"""
Copyright (c) 2019 Imdat Solak
                All Rights Reserved
"""
class SpacySIM(MLSimilarity):
    def __init__(self, configDictionary):
        super(SpacySIM, self).__init__(configDictionary)
        self.profile = {
                "name" : "spacy-module",
                "class" : "nlp-deepnn-analysis",
                "supported_request_types" : ["text"],
                "supported-languages" : ['de', 'en']
                }
        self.logger = logging.getLogger(os.path.basename(sys.argv[0]))
        self.maxSim = int(utils.getKeyFromSectionInConfiguration('similarity', 'max_similarity_to_return', 1, configDictionary))
        self.language_model = utils.getKeyFromSectionInConfiguration('similarity', 'language_model', 'de_core_news_sm', configDictionary)
        self.simLowerThreshold = float(utils.getKeyFromSectionInConfiguration('similarity', 'similarity_lower_threshold', 0.5, configDictionary))
        self.simHigherThreshold = float(utils.getKeyFromSectionInConfiguration('similarity', 'similarity_higher_threshold', 0.7, configDictionary))
        self.configDictionary = configDictionary
        self.update_lock = threading.Lock()
        self.alldocs = None

    def initForBender(self, benderInstance):
        self.benderCore = benderInstance
        self.nlp = self.benderCore.nlpModule()
        self._train()

    def _train(self):
        self.update_lock.acquire()
        self.alldocs = []
        allQ = self.benderCore.getBrain().getAllQuestions()
        for q in allQ:
            self.alldocs.append(self.nlp.nlp(q))
        self.update_lock.release()

    def _get_sim(self, query, num_docs=None):
        if self.alldocs is None:
            return None

        sims = []
        doc = self.nlp.nlp(query)
        for i in range(len(self.alldocs)):
            sims.append([i, doc.similarity(self.alldocs[i])])

        sims = sorted(sims, key=lambda item: -item[1])
        if num_docs is not None and len(sims)>0:
            sims = sims[:min(num_docs, len(sims))]
        if len(sims)>0:
            return sims
        else:
            return None

    def getSimilarEntriesFromCorpus(self, query, enrichedQuery = '', num_sim = 0):
        logging.info('getSimilarEntriesFromCorpus: [%s]' % query)
        retArr = []
        if num_sim == 0:
            num_sim = self.maxSim + 5
        sims = self._get_sim(query, num_sim)
        if sims != None:
            logging.info('Found %d similars' % len(sims))
            jcHC = self.benderCore.higherConfidenceLevel()
            jcLC = self.benderCore.lowerConfidenceLevel()
            for sim in sims:
                similarityValue = float(sim[1])
                # We need to normalize them for BenderCore thresholds
                # Otherwise BenderCore will either reject or ask a Human
                logging.info('.......... index=%d, sim=%f' % (sim[0], similarityValue))
                if similarityValue >= self.simLowerThreshold:
                    if similarityValue >= self.simHigherThreshold:
                        multiplier = (1-jcHC) / (1-self.simHigherThreshold)
                        diff = similarityValue - self.simHigherThreshold
                        similarityValue = jcHC + (diff * multiplier)
                    else:
                        multiplier = (jcHC - jcLC) / (self.simHigherThreshold - self.simLowerThreshold)
                        diff = similarityValue - self.simLowerThreshold
                        similarityValue = jcLC + (diff * multiplier)
                    sim = (sim[0], similarityValue)
                    logging.info('.......... -> index=%d, sim=%f' % (sim[0], similarityValue))
                    retArr.append(sim)
        else:
            logging.info('Found no similar entries...')
        if len(retArr):
            return retArr
        else:
            return None

    def addNewQAPair(self, questionData=None, answerData=None):
        if questionData is not None and len(questionData.keys())>0:
            qID = int(questionData.keys()[0])
            if qID >= len(self.alldocs):
                self.update_lock.acquire()
                self.alldocs.append(self.nlp.nlp(questionData[questionData.keys()[0]]['question']))
                self.update_lock.release()

