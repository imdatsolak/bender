# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import sys 
reload(sys)
sys.setdefaultencoding("utf-8")
from pymongo import MongoClient

import datetime
from modules.storage.permanentstorage.mlpermanentstorage import MLPermanentStorage
from core import utils

"""
The MongoDBStorage Module is an interface that allows
Bender to store statements in a MongoDB database.

Copyright (c) 2019 Imdat Solak
                All Rights Reserved.
"""
class MongoDBStorage(MLPermanentStorage):
    defaultOwner = 'NO_OWNER'

    def __init__(self, configDictionary):
        super(MongoDBStorage, self).__init__(configDictionary)
        self.database_name = utils.getKeyFromSectionInConfiguration('permanentstorage', 'mongodb_storage_database', 'bender_database', configDictionary)
        self.database_uri = utils.getKeyFromSectionInConfiguration('permanentstorage', 'mongodb_storage_database_uri', 'mongodb://localhost:27017/', configDictionary)
        self.client = MongoClient(self.database_uri)
        self.database = self.client[self.database_name]
        self.entries = self.database['benderentries']
        # We need to create indexes, but this is left for later...
        # self.statements.create_index('ownerID', unique=True)
        self.profile = {   
                            "name" : "mongodb-storage",
                            "class" : "permanent-storage",
                            "verson" : "1.0"
                        }

    def capabilities(self):
        return self.profile

    def count(self):
        return self.entries.count()

    def find(self, ownerID, key):
        entry = self.entries.find_one({"ownerID" : ownerID, "key" : key})
        if entry:
            return entry['data']
        return None

    def storeDataForKey(self, data, key, ownerID = "NO_OWNER", timeLimitInSeconds = 1000*365*24*60*60):
        expirationDate = datetime.datetime.utcnow() + datetime.timedelta(seconds=timeLimitInSeconds)
        updateData = {
                    "ownerID" : ownerID,
                    "key" : key, 
                    "data": data,
                    "expirationDate" : expirationDate,
                    "lastAccessTime" : datetime.datetime.utcnow(),
                    }
        entry = self.entries.find_one({"ownerID" : ownerID, "key": key})
        if entry:
            self.entries.update_one({"_id": entry['_id']}, toInsert)
        else:
            self.entries.insert_one(updateData)
        return True

    def updateLastAccessTimeOfDataForKeyAndOwner(self, key, ownerID):
        entry = self.entries.find_one({"ownerID" : ownerID, "key": key})
        if entry:
            self.entries.update({'_id': entry['_id']}, {'$set':{'lastAccessTime': datetime.datetime.utcnow()}})
            return True
        return False

    def updateTimelimitOfDataWithKeyAndOwner(self, newTimeLimitInSeconds, key, ownerID):
        entry = self.entries.find_one({"ownerID" : ownerID, "key": key})
        if entry:
            self.entries.update({'_id': entry['_id']}, {'$set':{'expirationDate': datetime.datetime.utcnow() + datetime.timedelta(seconds=newTimeLimitInSeconds)}})
            return True
        return False

    def updateTimelimitOfAllDataForOwner(self, newTimeLimitInSeconds, ownerID):
        entries = self.entries.find_one({"ownerID" : ownerID, "key": key})
        if entries:
            for entry in entries:
                self.entries.update({'_id': entry['_id']}, {'$set':{'expirationDate': datetime.datetime.utcnow() + datetime.timedelta(seconds=newTimeLimitInSeconds)}})
            return True
        return False

    def deleteDataForKey(self, key, ownerID = "NO_OWNER"):
        self.entries.remove({'ownerID': defaultOwner, 'key' : key})
        return True

    def deleteAllDataForOwner(self, ownerID):
        self.entries.remove({'ownerID': ownerID})
        return True

    def dataForKeyAndOwner(self, key, ownerID = "NO_OWNER"):
        return self.find(ownerID, key)

    def lastAccessTimeForKeyAndOwner(self, key, ownerID):
        entry = self.entries.find_one({'ownerID': ownerID, 'key': key})
        if entry:
            return entry['lastAccessTime']
        return None

    def drop(self):
        """
        Remove the database.
        """
        self.client.drop_database(self.database_name)

