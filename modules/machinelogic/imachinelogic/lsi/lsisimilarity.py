# -*- coding: utf-8 -*-
from __future__ import print_function
import sys 
reload(sys)
sys.setdefaultencoding("utf-8")
from core import utils
from modules.machinelogic.imachinelogic.mlimachinelogic import MLInternalMachineLogic, MLInternalMachineLogicTrainer
from modules.machinelogic.imachinelogic.lsi.gensimmodel import GenSimModel
from modules.machinelogic.imachinelogic.lsi.gensimmodelgenerator import GenSimModelGenerator
import logging
import os
"""
Class TextSimilarity as described at:
    https://wiki.ml.de/display/DJ/Similarity+Module

Copyright (c) 2019 Imdat Solak
                All Rights Reserved

"""
class LSISimilarityTrainer(MLInternalMachineLogicTrainer):
    def __init__(self, moduleConfigSectgion, configDictionary, brain):
        self.configDictionary = configDictionary
        self.brain = brain

    def train(self):
        gensim_mg = GenSimModelGenerator(self.brain, self.configDictionary)
        gensim_mg.creat()

    def reTrain(self):
        pass


class LSISimilarity(MLInternalMachineLogic):
    def __init__(self, moduleConfigSection, configDictionary):
        super(LSISimilarity, self).__init__(moduleConfigSection, configDictionary)
        self.profile = {
                "name" : "lsi-module",
                "class" : "latent-semantic-analysis",
                "supported_request_types" : ["text"],
                "supported-languages" : ["de"]
                }
        self.module_config = moduleConfigSection
        self.config_dict = configDictionary
        self.logger = logging.getLogger(os.path.basename(sys.argv[0]))
        self.maxSim = int(self.module_config.get('max_similarity_to_return', 1))
        self.simLowerThreshold = float(self.module_config.get('similarity_lower_threshold', 0.5))
        self.simHigherThreshold = float(self.module_config.get('similarity_higher_threshold', 0.7))
        self.is_master = int(self.module_config.get('is-master', 0))
        self.contribution_factor = int(self.module_config.get('contribution-factor', 500))

    def initForBender(self, benderInstance):
        self.benderCore = benderInstance
        self.gensim_model = GenSimModel(self.benderCore.getBrain(), self.module_config, self.configDictionary)

    def isMaster(self):
        return self.is_master

    def contributionFactor(self):
        return self.contributionFactor

    def performTextQuery(self, query, num_sim=10, jobID=None):
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

    def reinforceCorrectResponse(self, query, response, inputMediaType, outputMediaType):
        self.addNewQAPair()
        return None, None

    def reinforceWrongResponse(self, query, response, inputMediaType, outputMediaType):
        self.addNewQAPair()
        return None, None

    def addNewQAPair(self, questionData=None, answerData=None):
        self.gensim_model.setRequiresRetraining(True)
        self.gensim_model.resetLearningTimer()

