# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import sys 
reload(sys)
sys.setdefaultencoding("utf-8")

import codecs
import json
import datetime
from core import utils
from modules.storage.mlstorage import MLStorage
"""
MLTransientStorage is the initial implementation of a transient storage class
Usage:
    storage = MLTransientStorage()
    storage.storeData...
    data = storage.dataForKey...
                             
Copyright (c) 2019 Imdat Solak
                    All Rights Reserved.

"""

class MLTransientStorage(MLStorage):
    def __init__(self, configDictionary):
        self.profile = {
                "name" : "mltransientstorage",
                "class" : "transient-storage"
                }
        self.entries = {}

    def initForBender(self, benderInstance):
        self.benderCore = benderInstance

    def count(self):
        return self.entries.count()

    def _findSimilar(self, ownerID, key):
        return 'Hello World', 0.99

    def _find(self, ownerID, key):
        if ownerID in self.entries:
            ownerData = self.entries[ownerID]
            if ownerData and key in ownerData.keys():
                entry = ownerData[key]
                if entry:
                    return entry['data']
        return None

    def _findAllForOwner(self, ownerID):
        if ownerID in self.entries:
            ownerData = self.entries[ownerID]
            retVal = {}
            for key in ownerData.keys():
                retVal[key] = ownerData[key]['data']
            return retVal
        return None

    def storeDataForKey(self, data, key, ownerID = "NO_OWNER", timeLimitInSeconds = 1000*365*24*60*60):
        expirationDate = datetime.datetime.utcnow() + datetime.timedelta(seconds=timeLimitInSeconds)
        updateData = { 
                        "data" : data,
                        "expirationDate" : expirationDate.strftime("%Y%m%d%H%M%S%f"),
                        "lastAccessTime" : datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
                    }
        if ownerID in self.entries:
            self.entries[ownerID][key] = updateData
        else:
            self.entries[ownerID] = { key : updateData }
        return True

    def updateLastAccessTimeOfDataForKeyAndOwner(self, key, ownerID):
        return False
        entry = self.entries[ownerID][key]
        if entry:
            self.entries[ownerID][key]['lastAccessTime'] = datetime.datetime.utcnow()
            return True
        return False

    def updateTimelimitOfDataWithKeyAndOwner(self, newTimeLimitInSeconds, key, ownerID):
        return False
        entry = self.entries[ownerID][key]
        if entry:
            self.entries[ownerID][key]['expirationDate'] = datetime.datetime.utcnow() + datetime.timedelta(seconds=newTimeLimitInSeconds)
            return True
        return False

    def updateTimelimitOfAllDataForOwner(self, newTimeLimitInSeconds, ownerID):
        return False
        entries = self.entries[ownerID]
        if entries:
            for key in entries.iteritems():
                self.entries[ownerID][key] =  datetime.datetime.utcnow() + datetime.timedelta(seconds=newTimeLimitInSeconds)
            return True
        return False

    def deleteDataForKey(self, key, ownerID = "NO_OWNER"):
        if self.entries[ownerID][key]:
            del self.entries[ownerID][key]
            return True
        return False

    def deleteAllDataForOwner(self, ownerID):
        if self.entries[ownerID]:
            del self.entries[ownerID]
        return True

    def dataForKey(self, key, ownerID = "NO_OWNER"):
        return self._find(ownerID, key)

    def allDataForOwner(self, ownerID):
        return self._findAllForOwner(ownerID)

    def similarDataForKey(self, key, ownerID = "NO_OWNER"):
        return self._findSimilar(ownerID, key)

    def lastAccessTimeForKeyAndOwner(self, key, ownerID):
        # entry = self.entries.find_one({'ownerID': ownerID, 'key': key})
        # if entry:
         #    return entry['lastAccessTime']
        return None

