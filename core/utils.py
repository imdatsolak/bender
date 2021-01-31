# -*- coding: utf-8 -*-
import sys 
reload(sys)
sys.setdefaultencoding("utf-8")
import random
import datetime
import os
import ConfigParser
import logging
import getopt
import re
from nltk.tokenize import word_tokenize, sent_tokenize
"""
Bender utility functions
Copied from ChatterBot: https://github.com/gunthercox/ChatterBot
Copyright (c) 2016 gunthercox
All Rights Reserved

This is a collection of functions that are used internally by BenderCore, especially
for loading modules...

Copyright (c) 2019 Imdat Solak

Created: 2017-04-09 10:00 CET, ISO

"""
BENDER_LOG_FORMAT = '%(asctime)-15s %(classname)s : %(message)s'
punkt_remover = re.compile(r'[0-9“”.,;:\'"/?!@#$%&*()\-_=+\[\]\{\}~`<>`\n\t]+')
def clean_whitespace(text):
    """
    Remove any extra whitespace and line breaks as needed.
    """
    import re
    # Replace linebreaks with spaces
    text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    # Remove any leeding or trailing whitespace
    text = text.strip()
    # Remove consecutive spaces
    text = re.sub(' +', ' ', text)
    return text


def clean(text):
    """
    A function for cleaning a string of text.
    Returns valid ASCII characters.
    """
    import unicodedata
    import sys
    text = clean_whitespace(text)
    # Replace HTML escape characters
    if sys.version_info[0] < 3:
        from HTMLParser import HTMLParser
        parser = HTMLParser()
        text = parser.unescape(text)
    else:
        import html
        text = html.unescape(text)
    # Normalize unicode characters
    # 'raw_input' is just 'input' in python3
    if sys.version_info[0] < 3:
        text = unicode(text)
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    return str(text)


def import_module(dotted_path):
    """
    Imports the specified module based on the
    dot notated import path for the module.
    """
    import importlib
    module_parts = dotted_path.split('.')
    module_path = '.'.join(module_parts[:-1])
    module = importlib.import_module(module_path)
    return getattr(module, module_parts[-1])


def initialize_class(data, configDictionary):
    """
    :param data: A string or dictionary containing a import_path attribute.
    """
    if isinstance(data, dict):
        import_path = data.pop('import_path')
        data.update(configDictionary)
        Class = import_module(import_path)
        return Class(**data)
    else:
        Class = import_module(data)
        return Class(configDictionary)


def initialize_training_class(data, brain, configDictionary):
    """
    :param data: A string or dictionary containing a import_path attribute.
    """
    if isinstance(data, dict):
        import_path = data.pop('import_path')
        data.update(configDictionary)
        Class = import_module(import_path)
        return Class(**data)
    else:
        Class = import_module(data)
        return Class(brain, configDictionary)


def initialize_class_with_config_section(data, configSection, configDictionary, **kwargs):
    """
    :param data: A string or dictionary containing a import_path attribute.
    """
    if isinstance(data, dict):
        import_path = data.pop('import_path')
        data.update(configDictionary)
        Class = import_module(import_path)
        return Class(**data)
    else:
        Class = import_module(data)
        return Class(configSection, configDictionary, **kwargs)


def validate_module_class(validate_class, module_class):
    """
    Raises an exception if validate_class is not a
    subclass of module_class.

    :param validate_class: The class to be validated.
    :type validate_class: class

    :param module_class: The class type to check against.
    :type module_class: class

    :raises: InvalidmoduleException
    """
    from modules.mlbendermodule import MLBenderModule
    from .bendercore import BenderCore
    # If a dictionary was passed in, check if it has an import_path attribute
    if isinstance(validate_class, dict):
        origional_data = validate_class.copy()
        validate_class = validate_class.get('import_path')
        if not validate_class:
            raise BenderCore.InvalidModuleException(
                'The dictionary {} must contain a value for "import_path"'.format(
                    str(origional_data)
                )
            )
    if not issubclass(import_module(validate_class), MLBenderModule):
        raise BenderCore.InvalidModuleException(
            '{} must be a subclass of {}'.format(
                validate_class,
                MLBenderModule.__name__
            )
        )
    if not issubclass(import_module(validate_class), module_class):
        raise BenderCore.InvalidModuleException(
            '{} must be a subclass of {}'.format(
                validate_class,
                module_class.__name__
            )
        )


def getUniqueID(insertAtEnd = 100):
    now = datetime.datetime.utcnow()
    numbers = [now.year, now.month, now.day, now.hour, now.minute, now.second, now.microsecond, random.randint(0, 10000000), insertAtEnd]
    newUniqueID = ''.join('{:02X}'.format(a+random.randint(1, 999999)) for a in numbers)
    return newUniqueID

    
def getKeyFromSectionInConfiguration(section, key, defaultValue, configDictionary):
    if section in configDictionary:
        val = configDictionary[section]
        if key in val:
            return val[key]

    return defaultValue

    
def getModulenameFromConfiguration(key, defaultValue, configDictionary):
    return getKeyFromSectionInConfiguration(key, 'module', defaultValue, configDictionary)


def getTrainingModulenameFromConfiguration(key, defaultValue, configDictionary):
    return getKeyFromSectionInConfiguration(key, 'training_module', defaultValue, configDictionary)


def getSectionFromConfiguration(section, defaultValue, configDictionary):
    if section in configDictionary:
        return configDictionary[section]
    else:
        return defaultValue


def safe_create_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def getBenderConfiguration(configFile, verbose=False, debug=False):
    benderConfig = {}
    def getConfigOptionsForSection(config, section):
        retDict = {}
        for item in config.items(section):
            retDict[item[0]] = config.get(section, item[0])
        return retDict

    def extractConfigOptionsForSection(config, section):
        retDict = getConfigOptionsForSection(config, section)
        if retDict:
            benderConfig[section] = retDict

    if configFile:
        config = ConfigParser.ConfigParser()
        try:
            config.readfp(open(configFile))
        except:
            print("Confing File <", configFile, "> could not be read")
            sys.exit(1)
    else:
        print("Please provide a config file with the -c option")
        sys.exit(1)
    for section in config.sections():
        extractConfigOptionsForSection(config, section)

    mls = []
    imls = []
    des = []
    dps = []
    preprocs = []
    for section in config.sections():
        if section.startswith('i-machinelogic'):
            imls.append(section)
        elif section.startswith('machinelogic'):
            mls.append(section)
        elif section.startswith('dataprovider'):
            dps.append(section)
        elif section.startswith('dataextractor'):
            des.append(section)
        elif section.startswith('preprocessor'):
            preprocs.append(section)

    iMachineLogicEngines = []
    for i in range(0, len(imls)):
        section = 'i-machinelogic-' + str(i)
        retDict = getConfigOptionsForSection(config, section)
        iMachineLogicEngines.append(retDict)

    benderConfig['i-machinelogic'] = iMachineLogicEngines

    machineLogicEngines = []
    for i in range(0, len(mls)):
        section = 'machinelogic-' + str(i)
        retDict = getConfigOptionsForSection(config, section)
        machineLogicEngines.append(retDict)
    benderConfig['machinelogic'] = machineLogicEngines

    dataProviders = []
    for i in range(0, len(dps)):
        section = 'dataprovider-' + str(i)
        retDict = getConfigOptionsForSection(config, section)
        dataProviders.append(retDict)
    benderConfig['dataproviders'] = dataProviders

    dataExtractors = []
    for i in range(0, len(des)):
        section = 'dataextractor-' + str(i)
        retDict = getConfigOptionsForSection(config, section)
        dataExtractors.append(retDict)
    benderConfig['dataextractors'] = dataExtractors

    preprocessors = []
    for i in range(0, len(preprocs)):
        section = 'preprocessor-' + str(i)
        retDict = getConfigOptionsForSection(config, section)
        preprocessors.append(retDict)
    benderConfig['preprocessors'] = preprocessors

    benderConfig['bender-dev']['verbose'] = verbose
    benderConfig['bender-core']['verbose'] = verbose
    benderConfig['bender-dev']['debug'] = debug
    benderConfig['bender-core']['debug'] = debug
    return benderConfig


def multi_sent_tokenize(text, return_as_single_array = False):
    global punkt_remover
    result = []
    if isinstance(text, list):
        aText = ''
        for row in text:
            aText += row + '\n'
    else:
        atext = text
    for sent in sent_tokenize(line):
        sent = punkt_remover.sub('', sent)
        if return_as_single_array:
            result.extend(word_tokenize(sent))
        else:
            result.append(word_tokenize(sent))
    return result


def simple_tokenize(line):
    line = punkt_remover.sub('', line)
    return word_tokenize(line)


