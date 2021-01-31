# -*- coding: utf-8 -*-
from __future__ import print_function
import sys 
reload(sys)
sys.setdefaultencoding("utf-8")

from core import utils
import os
import codecs
import pickle
import threading
import logging
from time import sleep
import hashlib
from nltk.tokenize import RegexpTokenizer
from stop_words import get_stop_words
from gensim import corpora
import gensim

from core.progressbar import ProgressBar, Percentage, Bar, ETA, FormatLabel, AnimatedMarker
from modules.mlbendermodule import MLBenderModule
from modules.nlp.mlnlp import MLNLP
from modules.concept.mlconcept import MLConcept
from core.utils import simple_tokenize, multi_sent_tokenize

wordTokenizer = RegexpTokenizer(u'\w+')

brain_mutex = threading.Lock()
brain_add_mutex = threading.Lock()
def save_brain_data(data_storage_path, questions, answers, questions_indexed, answers_indexed):
    """
    This function is used to save the brain-data in a separate thread during Bender operations.
    The problem otherwise would be that, depending on data size, the user has to wait for his
    response quite some time (until save is finished).
    The reason: Once BenderCore receives an answer from a HumanLogic, it tells the brain and
    other modules to "learn" new data. After this learning, the brain needs to save itself to
    hard disk, otherwise the data would get lost. Since this call happens in BenderCore just
    in the "getResponse"-call, the return of the response to the REST-API would need to wait
    until this save has been done.

    Therefore, we do it in a separate thread.

    It has actually no drawback as the newly learned data is still in RAM and can immediately
    be used for next requests... (quite different from how it works in TextSimilarity and WMD)
    """
    logger = logging.getLogger(os.path.basename(sys.argv[0]))
    logger.info('Updating BRAIN DATA. Trying to get a mutex-lock...')
    brain_mutex.acquire()
    logger.info('Updating BRAIN DATA. successfully got a mutex-lock...')
    try:
        utils.safe_create_directory(data_storage_path)

        data_file = os.path.join(data_storage_path, 'knowledge-raw.pickle')
        knowledge = {'questions': questions, 'answers': answers}
        pickle.dump(knowledge, open(data_file, 'wb'))

        data_file = os.path.join(data_storage_path, 'knowledge-indexed.pickle')
        knowledge = {'questions': questions_indexed, 'answers': answers_indexed}
        pickle.dump(knowledge, open(data_file, 'wb'))

        logger.info('Updating BRAIN DATA: Successfully updated brain-data...')
    finally:
        brain_mutex.release()


def iter_dictionary_documents(top_directory, remove_stop_words=True, stop_words=None):
    """
    Iterate over all documents, yielding a document (=list of utf8 tokens) at a time.
    Updated: 2016-12-29 13:28 CET, ISO
             Fixed so many bugs, unbelievable :-()
    """
    global wordTokenizer
    errfile = codecs.open('/tmp/dict-errs.txt', 'w', 'utf-8')
    if remove_stop_words and not stop_words:
        stop_words = get_stop_words('en')
    for root, dirs, files in os.walk(top_directory):
        counter = 0
        widgets=[FormatLabel('   | File: %(message)s [%(value)s/'+str(len(files))+']'), ' ', Percentage(), ' ', Bar(marker='@', left='[', right=']'), ' ', ETA()]
        files.sort()
        pBar = ProgressBar(widgets=widgets, maxval=len(files)).start()
        for filename in filter(lambda filename: filename.endswith('.txt'), files):
            counter += 1
            pBar.update(counter, filename)
            filename = os.path.join(root, filename)
            lines = codecs.open(filename, 'r', 'utf-8').readlines() # read the entire file as an array of strings
            for line in lines:
                if '\t' in line:
                    # we don't need the questionID for the moment...
                    questionID, content = line.split('\t')
                else:
                    content = line
                content = content.strip().lower()
                # content = ' '.join(content.split('\n')).lower() # join lines into one big string (just to make sure)
                try:
                    # tokens = wordTokenizer.tokenize(content)
                    tokens = gensim.utils.simple_preprocess(content)
                    if remove_stop_words is True:
                        stopped_tokens = [i for i in tokens if not i in stop_words]
                    else:
                        stopped_tokens = tokens
                    yield stopped_tokens
                except:
                    print('Token error in file [', filename, ']', file=errfile)
        pBar.finish()
    errfile.close()

def convert_train_data(brain):
    questions = brain.getAllQuestions()
    for i, question in enumerate(questions):
        tokens = multi_sent_tokenize(question.strip().lower().split('\n'), return_as_single_array = True)
        # gensim has issues with German words that a bit longer than usual
        # text = ' '.join(question.strip().lower().split('\n'))
        # text = text.strip()
        # tokens = gensim.utils.simple_preprocess(text)
        question_id = str(i)
        yield question_id, tokens

"""
TrainingCorpus is a memory-friendly corpus generator to be used for training only.
Created: 2016-04-28 ??:?? CET, ISO
"""
class TrainingCorpus(gensim.corpora.TextCorpus):
    def __init__(self, brain, dictionary, remove_stop_words=True, stop_words=None, **kwargs):
        super(TrainingCorpus, self).__init__(**kwargs)
        self.brain = brain
        self.dictionary = dictionary
        self.remove_stop_words = remove_stop_words
        self.stop_words = stop_words

    def get_texts(self):
        """
        Iterate over all documents, yielding a document (=list of utf8 tokens) at a time.
        Updated: 2016-12-29 13:28 CET, ISO
                 Fixed so many bugs, unbelievable :-()
        """
        global wordTokenizer
        length = 0
        questions = self.brain.getAllQuestions()
        for i, question in enumerate(questions):
            content = gensim.utils.to_utf8(' '.join(question.strip().lower().split('\n')).strip())
            try:
                tokens = gensim.utils.simple_preprocess(content)
                # tokens = simple_tokenize(content)
                if self.remove_stop_words is True:
                    stopped_tokens = [i for i in tokens if not i in self.stop_words]
                else:
                    stopped_tokens = tokens
                length += 1
                yield stopped_tokens
            except:
                print('Token error in file [', content, ']')
        self.length = length


"""
class DictionaryInitializer

Generates a dictionary from files
This is a memory-friendly version of a dictionary generator...

"""
class GensimDictionary(object):
    def __init__(self, dictionary_data_root_dir, dictionary_filename, remove_stop_words=True, stop_words=None):
        self.dict_filename = dictionary_filename
        self.remove_stop_words = remove_stop_words
        self.stop_words = stop_words
        if not os.path.exists(dictionary_filename):
            print("   | Generating dictionary from file %s..." % dictionary_data_root_dir)
            self.dictionary = corpora.Dictionary(iter_dictionary_documents(dictionary_data_root_dir, remove_stop_words, stop_words))
            self.dictionary.filter_extremes(no_below=0, no_above=0.1, keep_n=10000000)
            # self.dictionary.compactify()
            self.saveDictionary()
        self.loadDictionary()

    def saveDictionary(self):
        self.dictionary.save(self.dict_filename)

    def loadDictionary(self):
        self.dictionary = corpora.Dictionary.load(self.dict_filename)

    def addWords(self, textArray):
        global wordTokenizer
        documentsToAdd = []
        for document in textArray:
            text = ' '.join(document.strip().lower().split('\n'))
            tokens = wordTokenizer.tokenize(text)
            if self.remove_stop_words is True:
                stopped_tokens = [i for i in tokens if not i in self.stop_words]
            else:
                stopped_tokens = tokens
            documentsToAdd.append(stopped_tokens)
        self.dictionary.add_documents(documentsToAdd, prune_at=None)


    def getDictionary(self):
        return self.dictionary


"""
Class MLBrain as described at:
    https://wiki.ml.de/display/DJ/Bender+Brain

Copyright (c) 2019 Imdat Solak
                All Rights Reserved

Created: 2017-04-29 10:32 CET, ISO
"""
class MLBrain(MLBenderModule):
    def __init__(self, configDictionary):
        super(MLBrain, self).__init__(configDictionary)
        self.profile = {
                "name" : "mlbrain-module",
                "class" : "mlbrain"
                }
        self.nlp_module = None
        self.concept_module = None
        self.data_storage_path = utils.getKeyFromSectionInConfiguration('brain', 'data_storage_path', None, configDictionary)
        self.dictionary_data_source_path = utils.getKeyFromSectionInConfiguration('bender-training', 'dictionary_data_source_path', None, configDictionary)
        self.dictionary_output_path = utils.getKeyFromSectionInConfiguration('bender-training', 'dictionary_output_path', None, configDictionary) 
        if self.dictionary_output_path == None:
            print('**** ERROR: No Dictionary output path defined in bender-training section of config-file.')
            sys.exit(1)
        self.dict_filename = os.path.join(self.dictionary_output_path, 'dictionary.dict')
        self.remove_stop_words = int(utils.getKeyFromSectionInConfiguration('bender-training', 'remove_stop_words', '0', configDictionary))
        self.language = utils.getKeyFromSectionInConfiguration('bender-training', 'data_language_short', 'en',configDictionary)        
        self.stop_words = get_stop_words(self.language)
        utils.safe_create_directory(self.dictionary_output_path)
        if self.data_storage_path == None:
            print('**** ERROR: No data storage path specified. Exiting!')
            sys.exit(1)
        self.dictionary_manager = GensimDictionary(self.dictionary_data_source_path, self.dict_filename, self.remove_stop_words, self.stop_words)
        self._loadData()

    def initForBender(self, benderInstance):
        self.benderCore = benderInstance

    def _text_as_index(self, text):
        global wordTokenizer
        q = ' '.join(text.lower().split('\n'))
        qArr = wordTokenizer.tokenize(q)
        q = ' '.join(qArr)
        return hashlib.sha256(q).hexdigest()

    def _question_as_index(self, question):
        return self._text_as_index(question)

    def _answer_as_index(self, answer):
        return self._text_as_index(answer)

    def _addNewQAPair(self, question, answer, qType='e', qCategory = 1, mcugAnswers = {}):
        """
        Same as 'batchAddNewQAPairs', except it works on a single QA-Pair
        questionAnswerPair is a tuple (Q, A)
        """
        if question != None and answer != None:
            newQuestion = question
            appendQuestion = False
            appendAnswer = False
            qIndexHash = self._question_as_index(question['question'])
            if qIndexHash in self.questions_indexed.keys():
                newQuestionID = self.questions_indexed[qIndexHash]
            else:
                newQuestionID = len(self.questions)
                appendQuestion = True

            aIndexHash = self._answer_as_index(answer)
            # Do we alrady have the answer stored?
            if aIndexHash in self.answers_indexed.keys():
                # Yes, then throw away the data and just retrieve existing index
                newAnswerID = self.answers_indexed[aIndexHash]
            else:
                # No? then we need to add it
                newAnswerID = len(self.answers)
                appendAnswer = True

            if mcugAnswers == None:
                mcugAnswers = {} 

            if appendQuestion:
                newQuestion = question
                newQuestion['answers'] = [newAnswerID]
                newQuestion['qType'] = qType
                newQuestion['category'] = qCategory
                newQuestion['qID'] = newQuestionID
                if 'answerID' in newQuestion.keys():
                    del newQuestion['answerID']
                self.questions.append(newQuestion)
                self.questions_indexed[qIndexHash] = newQuestionID
            retAnswer = {'id': newAnswerID, 'answer': answer, 'mcugAnswers': mcugAnswers}
            if appendAnswer:
                self.answers.append(retAnswer)
                self.answers_indexed[aIndexHash] = newAnswerID

            return {newQuestionID: newQuestion}, retAnswer 
        else:
            return None, None

    def setNLPModule(self, nlpModule):
        self.nlp_module = nlpModule

    def setConceptModule(self, conceptModule):
        self.concept_module = conceptModule

    def addNewQAPair(self, questionAnswerPair, qType='e', qCategory=1, mcugAnswers={}):
        brain_add_mutex.acquire()
        question = {'question': questionAnswerPair[0]}
        answer = questionAnswerPair[1]
        qI, aI = self._addNewQAPair(question, answer, qType, qCategory, mcugAnswers)
        if qI != None:
            text = question['question'] + ' ' + answer
            self.dictionary_manager.addWords([text])
            self.dictionary_manager.saveDictionary()
            self._saveData()
            brain_add_mutex.release()
            return qI, aI
        else:
            brain_add_mutex.release()
            return None, None

    def batchAddNewQAPairs(self, trainingData):
        """
        Stores 'questions' and 'answers' in its internal storage as indexed pairs
        IN:
            trainingData = PICKLE Format as output by 'convert_csv.py' or similar
            preparation tools
        """
        questions = trainingData['questions']
        answers = trainingData['defaultAnswers']
        mcugAnswers = trainingData['mcugAnswers']
        text = [] 
        for question in questions:
            qType = question['qType']
            category = question['category']
            answer = answers[question['answerID']]
            mcugAnswer = mcugAnswers.get(str(question['answerID']), None)
            self._addNewQAPair(question, answer, qType, category, mcugAnswer)
            textLine = question['question'] + ' ' + answer
            if mcugAnswer is not None:
                for key in mcugAnswer.keys():
                    value = mcugAnswer[key]
                    textLine = textLine + ' ' + value
            text.append(textLine)

        self.dictionary_manager.addWords(text)
        self.dictionary_manager.saveDictionary()
        self._saveData()
        return True

    def _index_questions(self, questions):
        result = {}
        for i, entry in enumerate(questions):
            hashIndex = self._question_as_index(entry['question'])
            result[hashIndex] = i
        return result

    def _index_answers(self, answers):
        result = {}
        for i, entry in enumerate(answers):
            hashIndex = self._answer_as_index(entry)
            result[hashIndex] = i
        return result

    def _loadData(self):
        self.questions = []
        self.answers = []
        self.questions_indexed = {}
        self.answers_indexed = {}
        data_file = os.path.join(self.data_storage_path, 'knowledge-raw.pickle')
        if os.path.exists(data_file):
            knowledge = pickle.load(open(data_file, 'rb'))
            self.questions = knowledge['questions']
            self.answers = knowledge['answers']
            data_file = os.path.join(self.data_storage_path, 'knowledge-indexed.pickle')
            if os.path.exists(data_file):
                knowledge = pickle.load(open(data_file, 'rb'))
                self.questions_indexed = knowledge['questions']
                self.answers_indexed = knowledge['answers']
            else:
                self.questions_indexed = self._index_questions(self.questions)
                self.answers_indexed = self._index_answers(self.answers)
                knowledge = {'questions': self.questions_indexed, 'answers': self.answers_indexed}
                pickle.dump(self.knowledge, open(data_file, 'wb'))

    def _saveData(self):
        # Because saving of the brain can take some time AFTER an update, we need to perform
        # it in a separate thread.
        # This is no problem as the thread itself is using a mutex-lock
        a = []
        a.extend(self.answers)
        q = []
        q.extend(self.questions)
        qI = {}
        qI.update(self.questions_indexed)
        aI = {}
        aI.update(self.answers_indexed)
        save_thread = threading.Thread(target=save_brain_data, args=(self.data_storage_path, q, a, qI, aI))
        save_thread.start()

    def getAllQuestions(self):
        return [qaPair['question'] for qaPair in self.questions]

    def getAllAnswers(self):
        return self.answers

    def getAllQAPairs(self):
        return self.questions

    def getQuestionTexForQuestionID(self, questionID):
        if questionID < len(self.questions):
            return self.questions[questionID]['question']
        else:
            return None

    def getAnswerIDsForQuestionID(self, questionID):
        if questionID < len(self.questions):
            return self.questions[questionID]['answers']
        else:
            return None

    def getMCUGAnswerForQuestionID(self, questionID, client, channel=None, userGroup=None):
        return None

    def getMCUGAnswerForAnswerID(self, answerID, client, channel=None, userGroup=None):
        return None

    def getAnswerTextsForQuestionID(self, questionID):
        if questionID < len(self.questions):
            answerIDs = self.questions[questionID]['answers']
            answers = []
            for answerID in answerIDs:
                answer = self.answers[answerID]
                answers.append(answer['answer'])
            return answers
        else:
            return None

    def getAnswersForQuestionID(self, questionID):
        if questionID < len(self.questions):
            questionInfo = self.questions[questionID]
            answerIDs = questionInfo['answers']
            answers = []
            for answerID in answerIDs:
                anAnswer = self.answers[answerID]
                anAnswer['qType'] = questionInfo.get('qType', 'e')
                answers.append(anAnswer)
            return answers
        else:
            return None

    def getAnswerTextForAnswerID(self, answerID):
        if answerID < len(self.answers):
            return self.answers[answerID]
        else:
            return None

    def getIDForQuestionText(self, questionText):
        qIndexHash = self._question_as_index(questionText)
        if qIndexHash in self.questions_indexed.keys():
            return self.questions_indexed[qIndexHash]
        else:
            return None

    def getQuestionCount(self):
        return len(self.questions)

    def getAnswerCount(self):
        return len(self.answers)

    def getDictionary(self):
        return self.dictionary_manager.getDictionary()

    def getIndicesForText(self, text):
        """
        Returns an array of numbers consisting, in exactly the same order as the text, numbers representing the words.
        If it encounters a word it doesn't know the index (number) will be "-1"
        If you encounter such a word, you could first call the "addWordsToDictionary" with that word
        and call indicesForText again.
        ;text; is just a full text in UTF-8 format
        """
        global wordTokenizer
        text = text.lower()
        returnArray = []
        try:
            sentences = text.strip().lower().split('\n')
        except:
            return None
        dictionaryTokens = self.getDictionary().token2id
        for sentence in sentences: 
            row = []
            for token in wordTokenizer.tokenize(sentence):
                if token in dictionaryTokens:
                    row.append(dictionaryTokens[token])
                else:
                    row.append(-1)
            returnArray.append(row)
        return returnArray

    def getTextForIndices(self, indexArray):
        """
        Returns a UTF-8 string representing the indices exactly in the same order as they appeared in the
        indexArray. If the array contained an index that is out of the range of the module's dictionary,
        the word in question will be "<__((UNKNOWN))__>"
        ;indexArray; is a two-dimensional array; 1D = sentence; 2D=words in the sentence
        """
        returnArray = []
        for sentence in indexArray:
            newRow = ""
            for i in range(len(sentence)):
                wordID = sentence[i]
                wordText = self.getDictionary().get(wordID, '<__((UNKNOWN))__>')
                newRow = newRow + wordText + ' '
            returnArray.append(newRow)
        return returnArray

    def getStopWordCleanedText(self, text):
        global wordTokenizer
        if self.remove_stop_words:
            tokens = wordTokenizer.tokenize(text)
            stopped_tokens = [i for i in tokens if not i.lower() in self.stop_words]
            return ' '.join(stopped_tokens)
        else:
            return text

