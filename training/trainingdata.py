# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import sys 
reload(sys)
sys.setdefaultencoding("utf-8")
import os
import logging
import nltk.data
from core import utils
from core.progressbar import ProgressBar, Percentage, Bar, ETA, FormatLabel, AnimatedMarker
import codecs
from modules.brain.mlbrain import MLBrain
from modules.machinelogic.imachinelogic.mlimachinelogic import MLInternalMachineLogicTrainer
from modules.nlp.mlnlp import MLNLP
from modules.concept.mlconcept import MLConcept
from modules.mlbendertrainingmodule import MLBenderTrainingModule
import shutil
import pickle
import json

"""
Training-Data-Structure:

class TrainingDataConverter

Copyright (c) 2019 Imdat Solak

Written: 2017-04-12 00:00 CET, ISO

"""
class TrainingDataConverter(object):
    def __init__(self, configDictionary):
        self.configDictionary = configDictionary
        self.train_data_source_file = utils.getKeyFromSectionInConfiguration('bender-training', 'train_data_source_file', None, configDictionary)
        if not self.train_data_source_file:
            print("Config does not contain 'train_data_source_file', please provide one.")
            exit(1)

        self.query_media_type = utils.getKeyFromSectionInConfiguration('bender-training', 'query_media_type', None, configDictionary)
        self.response_media_type = utils.getKeyFromSectionInConfiguration('bender-training', 'response_media_type', None, configDictionary)
        self.raw_data_format = utils.getKeyFromSectionInConfiguration('bender-training', 'raw_data_format', None, configDictionary)
        self.train_data_q_media_type = utils.getKeyFromSectionInConfiguration('bender-training', 'train_data_q_media_type', None, configDictionary)
        self.train_data_a_media_type = utils.getKeyFromSectionInConfiguration('bender-training', 'train_data_a_media_type', None, configDictionary)
        self.output_path = utils.getKeyFromSectionInConfiguration('bender-training', 'output_path', None, configDictionary)
        self.train_data_queries_root_dir = utils.getKeyFromSectionInConfiguration('bender-training', 'converted_train_data_q_path', None, configDictionary)
        self.train_data_answers_dir = utils.getKeyFromSectionInConfiguration('bender-training', 'converted_train_data_a_path', None, configDictionary)
        self.generate_lsi = int(utils.getKeyFromSectionInConfiguration('bender-training', 'generate_lsi', 0, configDictionary))
        concept = utils.getModulenameFromConfiguration('concept', 'modules.concept.mlconcept.MLConcept', configDictionary)
        utils.validate_module_class(concept, MLConcept)
        self.concept = utils.initialize_class(concept, configDictionary)

        nlp = utils.getModulenameFromConfiguration('nlp', 'modules.nlp.mlnlp.MLNLP', configDictionary)
        utils.validate_module_class(nlp, MLNLP)
        self.nlp = utils.initialize_class(nlp, configDictionary)
        utils.safe_create_directory(self.output_path)
        self.configDictionary = configDictionary
        self.question_file = ''
        self.answers_file = ''
        self.questions = []
        self.answers = []
        self.internalMachineLogics = []

    def _initializeBrain(self):
        print('1/5: INITIALIZING --BRAIN-- :-)... & SPELLING ENGINE...')
        self.brain = MLBrain(self.configDictionary)
        self.brain.setNLPModule(self.nlp)
        self.brain.setConceptModule(self.concept)
        print("2/5: CONVERTING TRAINING DATA FROM SOURCE FORMAT AND ADDING TO --BRAIN--...")
        train_data = pickle.load(open(self.train_data_source_file, 'rb'))
        if train_data is not None:
            self.brain.batchAddNewQAPairs(train_data)

    def _initializeSimilarity(self):
        print("3/5: INITIALIZING SIMILARITY INDEXES...")
        if self.generate_lsi == 1:
            from modules.similarity.lsi.gensimmodelgenerator import GenSimModelGenerator
            gensim_generator = GenSimModelGenerator(self.brain, self.configDictionary)
            gensim_generator.create()

    def _trainInternalMachineLogics(self):
        print("4/5: TRAINING INTERNAL MACHINE LOGICS...")
        internalMLs = utils.getSectionFromConfiguration('i-machinelogic', None, self.configDictionary)
        for iml in internalMLs:
            module = iml['training_module']
            utils.validate_module_class(module, MLInternalMachineLogicTrainer)
            newInstance = utils.initialize_class_with_config_section(module, iml, self.configDictionary, brain=self.brain)
            newInstance.train()

    def _prepareNNIQAFormat(self):
        print("5/5: CONVERTING TRAINING DATA FOR NN in I-Q/A-FORMAT...")
        questions = []
        answers = {}
        self.answers = self.brain.getAllAnswers()
        self.questions = self.brain.getAllQAPairs()
        for entry in self.answers:
            answerText = entry['answer']
            aID = int(entry['id'])
            document = self.brain.getIndicesForText(answerText)
            arr = []
            for sentence in document:
                arr.extend(sentence)
            answers[aID] = arr
        questions = []
        for question in self.questions:
            qText = question['question']
            document = self.brain.getIndicesForText(qText)
            arr = []
            for sentence in document:
                arr.extend(sentence)
            questions.append({'question': arr, 'answers':question['answers']})
        output_p = os.path.join(self.output_path, 'nn_iqa')
        utils.safe_create_directory(output_p)
        output_qt = os.path.join(output_p, 'questions.json')
        output_qp = os.path.join(output_p, 'questions.pickle')
        output_at = os.path.join(output_p, 'answers.json')
        output_ap = os.path.join(output_p, 'answers.pickle')
        json.dump(questions, open(output_qt, 'w'), indent=4)
        json.dump(answers, open(output_at, 'w'), indent=4)
        pickle.dump(questions, open(output_qp, 'wb'))
        pickle.dump(answers, open(output_ap, 'wb'))

    def _prepareNNTrainData(self):
        self._prepareNNIQAFormat()
        return None

    def train(self):
        self._initializeBrain()
        self._initializeSimilarity()
        self._trainInternalMachineLogics()
        self._prepareNNTrainData()
        print("...done")
        print('SUMMARY:')
        print('\t[x] Dictionary Generation')
        print('\t[x] Questions-Corpus Generation')
        print('\t[x] Index-Generation (TfIfd & LSI)')
        print('\t[x] Conversion of question-text to dictionary-IDS')
        print('\t[x] Generation of a Word2Vec database (->%s/models)' % self.output_path)
        print('\t[x] Training of INTERNAL Neuronal Networks/i-Machine-Logic Engines')
        print('\t[ ] Training of EXTERNAL Neuronal Networks/MachineLogic Engines')
        print("----> Your EXTERNAL NEURONAL NETWORK training data is at: ", self.output_path, "/nn_iqa ...", sep='')

