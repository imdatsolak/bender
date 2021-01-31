# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import sys 
reload(sys)
sys.setdefaultencoding("utf-8")
import os.path
import datetime
import json
import threading
import codecs
from core import utils
from modules.storage.permanentstorage.mlpermanentstorage import MLPermanentStorage
"""
The JSONStorage Module is an interface that allows

NOTE:
    This is for testing purposes only, it is NOT RECOMMENDED AT ALL
    to use the JSONStorage for production!!!!

Copyright (c) 2019 Imdat Solak
                All Rights Reserved.
"""
class JSONStorage(MLPermanentStorage):
    defaultOwner = 'NO_OWNER'
    def __init__(self, configDictionary):
        super(JSONStorage, self).__init__(configDictionary)
        self.entries = {}
        jsonDatabaseFile = utils.getKeyFromSectionInConfiguration('permanentstorage', 'json_storage_database', '/tmp/-json-storage.json', configDictionary)
        self.mutex_lock = threading.Lock()
        self.jsonDataFile = jsonDatabaseFile
        self.profile = {   
                            "name" : "json-storage",
                            "class" : "permanent-storage",
                            "verson" : "1.0"
                        }
        if os.path.isfile(self.jsonDataFile):
            self.entries = json.load(codecs.open(self.jsonDataFile, 'r', 'utf-8'))
        else:
            utils.safe_create_directory(os.path.dirname(self.jsonDataFile))

    def capabilities(self):
        return self.profile

    def count(self):
        self.mutex_lock.acquire()
        count = self.entries.count()
        self.mutex_lock.release()
        return count

    def find(self, ownerID, key):
        retval = None
        self.mutex_lock.acquire()
        if ownerID in self.entries:
            ownerData = self.entries[ownerID]
            if ownerData and key in ownerData:
                entry = ownerData[key]
                if entry:
                    retval = entry['data']
        self.mutex_lock.release()
        return retval

    def storeDataForKey(self, data, key, ownerID = "NO_OWNER", timeLimitInSeconds = 1000*365*24*60*60):
        self.mutex_lock.acquire()
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
        # WARNING: self.saveDictionary() tries to acquire the same lock, thus 
        # we must release the lock BEFORE calling self.saveDictionary()
        self.mutex_lock.release()
        self.saveDictionary()
        return True

    def updateLastAccessTimeOfDataForKeyAndOwner(self, key, ownerID):
        self.mutex_lock.acquire()
        entry = self.entries[ownerID][key]
        if entry:
            self.entries[ownerID][key]['lastAccessTime'] = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
            self.mutex_lock.release()
            self.saveDictionary()
            return True
        else:
            self.mutex_lock.release()
            return False

    def updateTimelimitOfDataWithKeyAndOwner(self, newTimeLimitInSeconds, key, ownerID):
        self.mutex_lock.acquire()
        entry = self.entries[ownerID][key]
        if entry:
            self.entries[ownerID][key]['expirationDate'] = (datetime.datetime.utcnow() + datetime.timedelta(seconds=newTimeLimitInSeconds)).strftime("%Y%m%d%H%M%S%f")
            self.mutex_lock.release()
            self.saveDictionary()
            return True
        else:
            self.mutex_lock.release()
            return False

    def updateTimelimitOfAllDataForOwner(self, newTimeLimitInSeconds, ownerID):
        self.mutex_lock.acquire()
        entries = self.entries[ownerID]
        if entries:
            for key in entries.iteritems():
                self.entries[ownerID][key] =  (datetime.datetime.utcnow() + datetime.timedelta(seconds=newTimeLimitInSeconds)).strftime("%Y%m%d%H%M%S%f")
            self.mutex_lock.release()
            self.saveDictionary()
            return True
        else:
            self.mutex_lock.release()
            return False

    def deleteDataForKey(self, key, ownerID = "NO_OWNER"):
        self.mutex_lock.acquire()
        if self.entries[ownerID][key]:
            del self.entries[ownerID][key]
            self.mutex_lock.release()
            self.saveDictionary()
        else:
            self.mutex_lock.release()

    def deleteAllDataForOwner(self, ownerID):
        self.mutex_lock.acquire()
        if self.entries[ownerID]:
            del self.entries[ownerID]
            self.mutex_lock.release()
            self.saveDictionary()
        else:
            self.mutex_lock.release()

    def dataForKey(self, key, ownerID = "NO_OWNER"):
        # WARNING: Do NOT lock mutex here as 'self.find' will acquire the mutex
        return self.find(ownerID, key)

    def lastAccessTimeForKeyAndOwner(self, key, ownerID):
        # entry = self.entries.find_one({'ownerID': ownerID, 'key': key})
        # if entry:
         #    return entry['lastAccessTime']
        return None

    def saveDictionary(self):
        self.mutex_lock.acquire()
        entries_to_dump = {k:v for k,v in self.entries.items()}
        json.dump(entries_to_dump, codecs.open(self.jsonDataFile, 'w', 'utf-8'))
        self.mutex_lock.release()

    def drop(self):
        self.mutex_lock.acquire()
        self.entries.clear()
        self.mutex_lock.release()
        self.saveDictionary()

