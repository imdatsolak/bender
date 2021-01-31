# -*- encoding: utf-8 -*-
from __future__ import print_function
import sys
reload(sys)
sys.setdefaultencoding('utf-8')


"""
A superclass for all module classes.

Copyright (c) 2019 Imdat Solak
                All Rights Reserved
"""
class MLBenderModule(object):
    def __init__(self, configDictionary):
        self.benderCore = None
        self.profile = { 
                    "name" : "mlbender-module",
                    "class" : "generic-module"
                }   

    def capabilities(self):
        return self.profile

    def initForBender(self, benderInstance):
        """
        Gives the module access to an instance of the BenderCore class.
        """
        self.benderCore = benderInstance

    def getModuleName(self):
        return self.profile['name']

    def getModuleClass(self):
        return self.profile['class']

    class ModuleMethodNotImplementedError(NotImplementedError):
        """
        An exception to be raised when a module method has not been implemented.
        Typically this indicates that the developer is expected to implement the
        method in a subclass.
        """

        def __init__(self, message=None):
            """
            Set the message for the esception.
            """
            if not message:
                message = 'This method must be overridden in a subclass method.'
            self.message = message

        def __str__(self):
            return self.message

