# -*- coding: utf-8 -*-
import sys 
reload(sys)
import datetime
sys.setdefaultencoding("utf-8")

from core import utils
from nltk.tokenize import RegexpTokenizer
import datetime
import time
import logging
import string
import re
from modules.mlbendermodule import MLBenderModule
"""
Copyright (c) 2019 Imdat Solak
                All Rights Reserved
"""
punct_remover = re.compile('[%s]' % re.escape(string.punctuation))
class MLSession(MLBenderModule):
    sessionNo = 0
    def __init__(self, configDictionary):
        super(MLSession, self).__init__(configDictionary)
        self.profile = {
                "name" : "mlsession-module",
                "class" : "session",
                "session-timeout" : 10400
                }
        self.wordTokenizer = RegexpTokenizer(u'\w+')
        self.session_timeout = int(utils.getKeyFromSectionInConfiguration('session', 'session_timeout', self.profile['session-timeout'], configDictionary))
        self.sessions = {}

    def initForBender(self, benderInstance):
        self.benderCore = benderInstance

    def capabilities(self):
        return self.profile
  
    def _checkExpiredSessions(self):
        expired = []
        now = datetime.datetime.now()
        nowInSeconds = time.mktime(now.timetuple())
        for sessionID, sessionData in self.sessions.iteritems():
            if sessionData['sessionTimeout'] < nowInSeconds:
                expired.append(sessionID)

        for sessionID in expired:
            del self.sessions[sessionID]
            self.benderCore.sessionExpired(sessionID)

    def newSession(self, clientID):
        """
        Creates a new session record in internal session structure
        Also, checks whether any session has expired and removes that from
        the internal structure.
        The sessionID is a pointer to a session structure that stores various
        data about the session, including the session stack.
        Returns a a sessionID (UTF-8)
        """
        self.sessionNo = self.sessionNo + 1
        sessionID = utils.getUniqueID(self.sessionNo)
        now = datetime.datetime.now()
        expiration = time.mktime(now.timetuple()) + self.session_timeout
        """
        A session consists of its ID, the session-stack, extractedData and the session timeout.
        """
        currentSession = {'sessionStack': [], 'sessionTimeout':expiration, 'extractedData': {}}
        self.sessions[sessionID] = currentSession
        self._checkExpiredSessions()
        return sessionID
  
    def endSession(self, sessionID):
        """
        Ends a session, i.e. it deletes all session-related information and deletes the sessionID
        It does nothing if the session with the sessionID doesn't exist
        """
        if sessionID in self.sessions.keys():
            del self.sessions[sessionID]
        self._checkExpiredSessions()
        return True
  
    def _refreshSessionTimeout(self, sessionID):
        if sessionID in self.sessions.keys():
            now = datetime.datetime.now()
            expiration = time.mktime(now.timetuple()) + self.session_timeout
            self.sessions[sessionID]['sessionTimeout'] = expiration

    def storeRequestForSession(self, originalRequest, sessionID):
        """
        When a new request comes in, it stores that request for future use.
        'originalRequest' is the request as sent by the end-user.
        Additionally, it extends the session timeout by the parameter 'session-timeout', i.e.,
        every time the session is updated with new data, its lifetime is extended
        Returns 'True' if stored successfully, otherwise returns False
        """
        if sessionID in self.sessions.keys():
            self.sessions[sessionID]['sessionStack'].append(originalRequest)
            self._refreshSessionTimeout(sessionID)
            return True
        else:
            return False
         
    def enrichRequestInSession(self, originalRequest, sessionID):
        """
        Enriches the originalRequest with data from the session.
        If the session has expired, it will return nil.
        Returns a UTF8-string.
        """
        global punct_remover
        if sessionID in self.sessions.keys():
            self._refreshSessionTimeout(sessionID)
            currentSessionStack = self.sessions[sessionID]['sessionStack']
        else:
            return originalRequest

        enrichedRequest = originalRequest
        tokens = self.wordTokenizer.tokenize(enrichedRequest)
        stackMax = len(currentSessionStack)-1
        stackCount = 0
        while stackCount <= 3 and stackMax >= 0:
            enrichedRequest = currentSessionStack[stackMax] + ' ' + enrichedRequest
            stackMax -= 1
            tokens = self.wordTokenizer.tokenize(enrichedRequest)
            stackCount += 1

        enrichedRequest = punct_remover.sub('', enrichedRequest)
        self._refreshSessionTimeout(sessionID)
        return enrichedRequest

    def sessionExists(self, sessionID):
        return sessionID in self.sessions.keys()

    def forgetDialog(self, sessionID):
        """
        Removes dialog-data (remembering of previous utterances of the user)
        """
        if sessionID in self.sessions.keys():
            self.sessions[sessionID]['sessionStack'] = []
            self._refreshSessionTimeout(sessionID)

    def storeExtractedDataInSession(self, dataDictionary, dataExtractorID, sessionID):
        """
        Stores the dataDictionary as JSON internally for the dataExtractor with the ID dataExtractorID
        The extracted data is stored in session because when a session expires, the extracted
        data is automatically deleted and we don't need to do anything special
        """
        if sessionID in self.sessions.keys():
            self.sessions[sessionID]['extractedData'][dataExtractorID] = dataDictionary
            self._refreshSessionTimeout(sessionID)

    def deleteExtractedDataInSession(self, dataExtractorID, sessionID):
        """
        Deletes any data that has been extracted during this session.
        This function is used by some extractors who only want to keep
        data for a single request (current one). If the data from previous requests
        (in the same session) are still remembered, they should then be removed.
        Normally, those Extractors would overwrite existing data and not add
        to any existing data. But if there was no data in the current request,
        they might want to remove any existing data from previous requests...
        """
        if sessionID in self.sessions.keys():
            if dataExtractorID in self.sessions[sessionID]['extractedData'].keys():
                del self.sessions[sessionID]['extractedData'][dataExtractorID]

    def getExtractedDataForDataExtractor(self, dataExtractorID, sessionID):
        """
        Returns a dictionary containing all data that has been extracted within the given session
        by the provided dataExtractor
        Returns None if nothing was extracted so far.
        """
        if sessionID in self.sessions.keys():
            retval = self.sessions[sessionID]['extractedData'].get(dataExtractorID, None)
            self._refreshSessionTimeout(sessionID)
            return retval
        return None

