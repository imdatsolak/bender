# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import sys 
reload(sys)
sys.setdefaultencoding("utf-8")
from modules.storage.mlstorage import MLStorage
"""
MLPermanentStorage is the initial implementation of a permanent storage class
It only supports "Local File" (JSON)
Usage:
    storage = MLPermanentStorage()
    storage.storeData...
    data = storage.dataForKey...
                             
Copyright (c) 2019 Imdat Solak
                    All Rights Reserved.

"""

class MLPermanentStorage(MLStorage):
    def __init__(self, configDictionary):
        super(MLPermanentStorage, self).__init__(configDictionary)
        self.profile = {
                "name" : "mlpermanentstorage-json",
                "class" : "permanent-storage"
                }

    def capabilities(self):
        return self.profile

    def initForBender(self, benderInstance):
        self.benderCore = benderInstance

    def storeDataForKey(self, data, key, ownerID = "NO_OWNER", timeLimitInSeconds = 1000*365*24*60*60):
        # Stores an arbitrary data in the permanent storage that can be accessed by the owner with the ownerID
        # The data is only stored "about" timeLimitInSeconds and afterwards purged
        # timeLimitInSeconds is the "minimum" storage time. The purge happens occasionally, so the data may
        # reside longer than specified, but not shorter
        # Returns 'True' if successful, otherwise 'False'
        return False
 
    def updateLastAccessTimeOfDataForKeyAndOwner(self, key, ownerID):
        # There is a "last access" time for each entry in the permanent storage module.
        # Using this method, you can update the last access time of that entry.
        # The time used is "now"
        return False
  
    def updateTimelimitOfDataWithKeyAndOwner(self, newTimeLimitInSeconds, key, ownerID):
        # Updates the timelimit of the entry to "now+timeLimitInSeconds"
        # returns True if the entry existed and update was successful
        # returns False otherwise
        return False
  
    def updateTimelimitOfAllDataForOwner(self, newTimeLimitInSeconds, ownerID):
        # Updates the timelimit of all entries of the ownerID to "now+newTimeLimitInSeconds"
        # This method is mainly used by the session module as it tracks when the last
        # communication within a session was.
        return False
  
    def deleteDataForKey(self, key, ownerID ="NO_OWNER"):
        # Deletes the data associated with the key that has NO ownerID
        return False
  
    def deleteAllDataForOwner(self, ownerID):
        # Deletes all data (with all keys) for the owner "ownerID"
        return False
  
    def dataForKey(self, key, ownerID="NO_OWNER"):
        # Returns the data associated with key and that has no ownerID
        return False
 
    def lastAccessTimeForKeyAndOwner(self, key, ownerID):
        # Returns the last time this entry was accessed (based on "updateLastAccessTime...")
        # returns nil if the entry doesn't exist
        return False
  
    def dataForKeyAndOwner(self, key, ownerID):
        # Returns the data associated with key and ownerID
        return False
  
