# -*- coding: utf-8 -*-
import sys 
reload(sys)
sys.setdefaultencoding("utf-8")
import spacy
import logging
import os
import types



"""
GenericNameDetector:
"""
class GenericNameDetector(object):
    FIRSTNAME = 'FIRSTNAME'
    LASTNAME = 'LASTNAME'
    FULLNAME = 'FULLNAME'
    GENERICNAME = 'GENERICNAME'
    MALE = 'MALE'
    FEMALE = 'FEMALE'
    UNKNOWN_GENDER = 'UNK'

    def __init__(self, nlp, femaleNamesFile=None, maleNamesFile=None, unisexNamesFile=None, lastNamesFile=None):
        self.logger = logging.getLogger(os.path.basename(sys.argv[0]))
        self.nlp = nlp
        if self.nlp == None:
            self.logger.critical('Error: YOU MUST provide an NLP-Engine to use. Exiting!')
            os._exit(1)

        # It is fine if you cannot provide a list of male/female/unisex & lastnames
        # but in such a case, don't expect 'magic'. We will then just try to detect
        # names, but will not be able to tell whether it is lastname or firstname
        # and also whether it is male, female or unknown

        self.unisexNames = None
        self.maleNames = None
        self.femaleNames = None
        self.lastNames = None

        if femaleNamesFile is not None:
            self._loadFemaleNames(femaleNamesFile)
        if maleNamesFile is not None:
            self._loadMaleNames(maleNamesFile)
        if unisexNamesFile is not None:
            self._loadUnisexNames(unisexNamesFile)
        if lastNamesFile is not None:
            self._loadLastNames(lastNamesFile)
        if lastNamesFile is None and unisexNamesFile is None and femaleNamesFile is None and maleNamesFile is None:
            self.use_names_db = False
        else:
            self.use_names_db = True


    def _loadNamesFile(self, namesFile):
        result = None
        try:
            allEntries = codecs.open(namesFile, 'r', 'utf-8').readlines()
            result = []
            for entry in allEntries:
                result.append(entry.strip())
        except:
            self.logger.warning('Could not load names file {}. Proceeding without such a file...'.format(namesFile))

        return result


    def _loadFemaleNames(self, femaleNamesFile):
        self.femaleNames = self._loadNamesFile(femaleNamesFile)
        

    def _loadMaleNames(self, maleNamesFile):
        self.maleNames = self._loadNamesFile(maleNamesFile)


    def _loadUnisexNames(self, unisexNamesFile):
        self.unisexNames = self._loadNamesFile(unisexNamesFile)

    
    def _loadLastNames(self, lastNamesFile):
        self.lastNames = self._loadNamesFile(lastNamesFile)


    def _identifyEntryType(self, entry):
        nameType = self.GENERICNAME
        gender = self.UNKNOWN_GENDER
        if self.unisexNames is not None and ent in self.unisexNames:
            gender = self.UNKNOWN_GENDER
            nameType = self.FIRSTNAME
        elif self.femaleNames is not None and ent in self.femaleNames:
            gender = self.FEMALE
            nameType = self.FIRSTNAME
        elif self.maleNames is not None and ent in self.maleNames:
            gender = self.MALE
            nameType = self.FIRSTNAME
        elif self.lastNames is not None and ent in self.lastNames:
            gender = self.UNKNOWN_GENDER
            nameType = self.LASTNAME

        return nameType, gender


    def detectNamesInText(self, text):
        """
        Detects any name using an NLP engine and/or own names-list and returns 
        an array containing a dictionary:
        return = [
                    {
                        'start': <start-pos>,
                        'type': <FIRSTNAME | LASTNAME | FULLNAME>,
                        'gender': <MALE | FEMALE | UNK>,
                        'text': <detected-text>
                    },
                    ...
                ]
        """
        foundEntries = None
        if isinstance(text, basestring):
            string_to_analyze = unicode(text)
            entities = self.nlp.recognizeEntitiesInText(string_to_analyze)
            if entities is not None:
                foundEntries = []
                foundAnything = False
                for entry in entities:
                    # print('Entity: ', entry)
                    if entry['label'] == 'PERSON':
                        entryAsString = entry['text']
                        # print('Found Entity: {} -> {}'.format(entry['label'], entry['text']))
                        gender = None
                        firstNameFound = False
                        lastNameFound = False
                        nameType = self.GENERICNAME
                        gender = self.UNKNOWN_GENDER
                        if self.use_names_db:
                            if ' ' in entryAsString:
                                nameParts = entryAsString.split(' ')
                                for namePart in nameParts:
                                    nameType, lGender = self._identifyEntryType(namePart)
                                    if nameType == self.LASTNAME:
                                        # If we have identified a last-name, we ignore the gender as that
                                        # will always be 'UNK' 
                                        lastNameFound = True
                                    elif nameType == self.FIRSTNAME:
                                        # If we have identified a firstname and we had NOT 
                                        # found out the gender of the person BEFORE, we remember the gender.
                                        # Unfortunately, especially in Europe you may have names such as
                                        #   Xaver Maria
                                        # where 'Xaver' is a male-name and 'Maria' is a female-name. In this case
                                        # the person in question is actually male, but has a female second name :-/
                                        # Thus, we should only remember it once (the first time); even when we
                                        # receive a new gender information on the second name, we should 
                                        # ignore it...
                                        firstNameFound = True
                                        if gender == None:
                                            gender = lGender
                                if firstNameFound and lastNameFound:
                                    nameType = self.FULLNAME
                                elif firstNameFound:
                                    nameType = self.FIRSTNAME
                                else:
                                    nameType = self.LASTNAME
                            else:
                                nameType, gender = self._identifyEntryType(entryAsString)
                        if nameType != None and gender != None:
                            foundEntries.append({'start': entry['start'], 'type': nameType, 'gender': gender, 'text': entryAsString})
                            foundAnything = True
                if not foundAnything:
                    foundEntries = None
        else:
            print('text = ', text, type(text))
            self.logger.info('GenericNameDetector can only analyze strings. Returning NONE')

        return foundEntries


