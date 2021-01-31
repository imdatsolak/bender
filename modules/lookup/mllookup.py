# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import sys 
reload(sys)
sys.setdefaultencoding("utf-8")
import hashlib
from modules.mlbendermodule import MLBenderModule
from modules.storage.mlstorage import MLStorage

"""
MLLookup is used for looking up entries in a hash list and return the found items.
Usage:
    lookupM = MLLookup()
    lookupM.initForBender(benderCore)
    response = lookupM.lookupRequest(request)
    if response is not None:
        return response
 
Copyright (c) 2019 Imdat Solak
              All Rights Reserved.
 
"""
class MLLookup(MLBenderModule):
    def __init__(self, configDictionary):
        self.profile = {
                    "name" : "ml-lookup-module",
                    "class" : "lookup",
                    "lookup-timeout" : 1000000
                }

    def initForBender(self, benderInstance):
        self.benderCore = benderInstance

    def lookupRequest(self, request):
        storageModule = self.benderCore.storageModule()
        key = hashlib.sha256(request).hexdigest()
        response = storageModule.dataForKey(key, self.profile['uid'])
        if response:
            storageModule.updateTimelimitOfDataWithKeyAndOwner(self.profile['lookup-timeout'], key, self.profile['uid'])
            storageModule.updateLastAccessTimeOfDataForKeyAndOwner(key, self.profile['uid'])
            return response
        return None

    def storeRequestAndResponse(self, request, response):
        storageModule = self.benderCore.storageModule()
        key = hashlib.sha256(request).hexdigest()
        return storageModule.storeDataForKey(data=response, key=key, ownerID=self.profile['uid'], timeLimitInSeconds=self.profile['lookup-timeout']) 
