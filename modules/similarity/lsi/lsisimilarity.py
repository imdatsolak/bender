# -*- coding: utf-8 -*-
from __future__ import print_function
import sys 
reload(sys)
sys.setdefaultencoding("utf-8")
from core import utils
from modules.similarity.mlsimilarity import MLSimilarity
from modules.similarity.lsi.gensimmodel import GenSimModel
import logging
import os
"""
Copyright (c) 2019 Imdat Solak
    All Rights Reserved
"""
class LSISimilarity(MLSimilarity):
    def __init__(self, configDictionary):
        super(LSISimilarity, self).__init__(configDictionary)
        self.profile = {
                "name" : "lsi-module",
                "class" : "latent-semantic-analysis",
                "supported_request_types" : ["text"],
                "supported-languages" : ["de"]
                }
        self.logger = logging.getLogger(os.path.basename(sys.argv[0]))
        self.maxSim = int(utils.getKeyFromSectionInConfiguration('similarity', 'max_similarity_to_return', 1, configDictionary))
        self.simLowerThreshold = float(utils.getKeyFromSectionInConfiguration('similarity', 'similarity_lower_threshold', 0.5, configDictionary))
        self.simHigherThreshold = float(utils.getKeyFromSectionInConfiguration('similarity', 'similarity_higher_threshold', 0.7, configDictionary))
        self.configDictionary = configDictionary

    def initForBender(self, benderInstance):
        self.benderCore = benderInstance
        self.gensim_model = GenSimModel(self.benderCore.getBrain(), self.configDictionary)

    def getSimilarEntriesFromCorpus(self, query, enrichedQuery = '', num_sim = 0):
        logging.info('getSimilarEntriesFromCorpus: [%s]' % query)
        retArr = []
        if num_sim == 0:
            num_sim = self.maxSim + 5
        sims = self.gensim_model.get_text_similarity(query, num_sim, 'lsi')
        if sims != None:
            logging.info('Found %d similars' % len(sims))
            jcHC = self.benderCore.higherConfidenceLevel()
            jcLC = self.benderCore.lowerConfidenceLevel()
            for sim in sims:
                similarityValue = float(sim[1])
                # We need to normalize them for benderCore thresholds
                # Otherwise benderCore will either reject or ask a Human
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
        self.gensim_model.setRequiresRetraining(True)
        self.gensim_model.resetLearningTimer()
