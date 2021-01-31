# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
import os
import ConfigParser
import logging
import getopt
import random
# FLASK Related imports
import json
from flask import Flask, Request, jsonify, make_response, request, abort, send_from_directory
from flask_restful import Api, Resource, reqparse, fields, marshal

# BENDER Core Import - Bender Core is the class that does the actual job
from core.bendercore import BenderCore
from core import utils

random.seed(42)
"""
This file contains Bender's main code to run it.
For training, use "bender-train.py"

Bender requires a configuration file and you must provide the full-path to the configuration file.
The configuration file defines certain parameters of Bender.

Usage:
    python mlbender.py -c <config-file>

Copyright (c) 2019 Imdat Solak
              All Rights Reserved.

 imdat
Note: we are using Flask for the API-implementation and flask_restful for all the
      RESTful API stuff.
"""

BENDER_VERSION = "2.0b"
BENDER_FULL_VERSION = "MLBender (NATHAN)" + BENDER_VERSION
# Our API endpoints all start with this ...
API_ROOT = '/api/v1'
verbose = False
debug = False
devServerIP = '127.0.0.1'
devServerPort = 5000
accessLogFile = 'bender-access.log'

if __name__ == '__main__':
    configFile = ''
    try:
        options, arguments = getopt.getopt(sys.argv[1:], 'dhc:vV', ['debug', 'help', 'config=', 'version', 'reset', 'verbose'])
    except getopt.GetoptError:
        print('Usage:')
        print('\tpython mlbender.py -v|--version] [-V|--verbose] [-d|--debug] -c|--config <config-file>')
        print("\tPlease use '-d' (debug-mode) only during development!!")
        sys.exit(2)

    for opt, arg in options:
        if opt == '-h':
            print('No Help yet')
            sys.exit(0)
        elif opt in ('-v', '--version'):
            print('BENDER version %s' % BENDER_VERSION)
            sys.exit(0)
        elif opt in ('-c', '--config'):
            configFile = arg
        elif opt in ('-V', '--verbose'):
            verbose = True
        elif opt in ('-d', '--debug'):
            debug = True
else:
    try:
        import mod_wsgi
        process_group = mod_wsgi.process_group
        configFile = os.path.join('configs', process_group + '.ini')
    except:
        print('ERROR: Cannot find config file...')
        sys.exit(1)

try:
    benderConfig = utils.getBenderConfiguration(configFile, verbose, debug)
except:
    print('ERROR: Cannot load configFile %s' % os.path.join(os.getcwd(), configFile))
    sys.exit(1)

benderConfig['bender-core']['version'] = BENDER_VERSION

if benderConfig['bender-dev']['dev-server-ip']:
    devServerIP = benderConfig['bender-dev']['dev-server-ip']

if benderConfig['bender-dev']['dev-server-port']:
    devServerPort = int(benderConfig['bender-dev']['dev-server-port'])

if benderConfig['bender-dev']['dev-server-access-log']:
    accessLogFile = benderConfig['bender-dev']['dev-server-access-log']


"""
This function generates an HTTP-Status 401 response to be returned. It is
called by the Resource-functions (get, put, post, ...) after unsuccesful
authorization.

Returns:
    HTTP-Response with status 401 (Unauthorized Access).
"""
def unauthorized():
    return {'message' : 'Unauthorized access'}, 401



"""
Class APIBenderConfiguration

It is an API class handling the '/configuration'-request.
It forwards the request to BenderCore and returns it's response
as a JSON-Structure
"""
class APIBenderConfiguration(Resource):
    def __init__(self):
        self.reqp = reqparse.RequestParser()
        self.reqp.add_argument('clientID', type=str, required=True)
        super(APIBenderConfiguration, self).__init__()

    def post(self):
        global benderCore
        return benderCore.benderConfiguration()

    def get(self):
        global benderCore
        return benderCore.benderConfiguration()




"""
Class APISession

It is an API class handling the '/session'-requests.
It forwards the request to BenderCore and returns it's response
as a JSON-Structure
"""
class APISession(Resource):
    def __init__(self):
        self.reqp = reqparse.RequestParser()
        self.reqp.add_argument('clientID', type=str, required=True)
        self.reqp.add_argument('UUID', type=str, required=False)
        super(APISession, self).__init__()

    def post(self):
        global benderCore
        return benderCore.newSession(self.reqp.parse_args())

    def get(self):
        global benderCore
        return benderCore.newSession(self.reqp.parse_args())

    def delete(self):
        global benderCore
        return benderCore.deleteSession(self.reqp.parse_args())



"""
Class APIQuery

It is an API class handling the '/query'-request.
It forwards the request to BenderCore and returns it's response
as a JSON-Structure
"""
class APIQuery(Resource):
    def __init__(self):
        self.reqp = reqparse.RequestParser()
        self.reqp.add_argument('clientID', type=str, required=True)
        self.reqp.add_argument('UUID', type=str, required=True)
        self.reqp.add_argument('queryInputType', type=str, required=True)
        self.reqp.add_argument('requestedResponseType', type=str, required=True)
        self.reqp.add_argument('queryText', type=str, required=False)
        self.reqp.add_argument('queryURL', type=str, required=False)
        super(APIQuery, self).__init__()

    def post(self):
        global benderCore
        return benderCore.performRequest(self.reqp.parse_args())



"""
Class APIJob

It is an API class handling the '/job'-requests.
It forwards the request to BenderCore and returns it's response
as a JSON-Structure
"""
class APIJob(Resource):
    def __init__(self):
        self.reqp = reqparse.RequestParser()
        self.reqp.add_argument('clientID', type=str, required=True)
        self.reqp.add_argument('jobID', type=str, required=True)
        super(APIJob, self).__init__()

    def post(self):
        global benderCore
        return benderCore.jobStatus(self.reqp.parse_args())

    def get(self):
        global benderCore
        return benderCore.jobStatus(self.reqp.parse_args())

    def delete(self):
        global benderCore
        return benderCore.deleteJob(self.reqp.parse_args())



"""
Class APIResponse

It is an API class handling the '/response'-request.
It forwards the request to BenderCore and returns it's response
as a JSON-Structure
"""
class APIResponse(Resource):
    def __init__(self):
        self.reqp = reqparse.RequestParser()
        self.reqp.add_argument('clientID', type=str, required=True)
        self.reqp.add_argument('jobID', type=str, required=True)
        super(APIResponse, self).__init__()

    def post(self):
        global benderCore
        return benderCore.getResponse(self.reqp.parse_args())

    def get(self):
        global benderCore
        return benderCore.getResponse(self.reqp.parse_args())



"""
Class APIReinforcedLearning

It is an API class handling the '/reinforce'-request.
It forwards the request to BenderCore and returns it's response
as a JSON-Structure
"""
class APIReinforcedLearning(Resource):
    def __init__(self):
        self.reqp = reqparse.RequestParser()
        self.reqp.add_argument('clientID', type=str, required=True)
        self.reqp.add_argument('UUID', type=str, required=True)
        self.reqp.add_argument('UQAPID', type=str, required=True)
        self.reqp.add_argument('reinforcement', type=str, required=True)
        super(APIReinforcedLearning, self).__init__()

    def post(self):
        global benderCore
        return benderCore.reinforceLearning(self.reqp.parse_args())



"""
Class HLIList & HLIAnswerItem

These classes are used to request the list of open questions in the queue
and answer one of them
The list of open items is thus:
    'requests' : {
            <requestID>: {
                'originalRequest': ...,
                'spellCheckedRequest': ...,
                'enrichedOriginalRequest': ...,
                'enrichedSpellCheckedRequest': ...,
                'conceptualizedRequest': ...,
                'conceptualizedSpellCheckedRequest': ...,
                'conceptualizedEnrichedOriginalRequest': ...,
                'conceptualizedEnrichedSpellCheckedRequest': ...,
                'calculatedResponses': {
                    <responseID> : {
                        'responseText': ...,
                        'confidenceLevel': 0...1,
                        'logicengine-name': ...,
                        'logicengine-class': ...,
                    },
                    ...
                }
            },
            ...
        }

The answer is a dictionary:
    {
        'requestID': <requestID>,
        'response' : {
            'responseText': ...,
            'qType': [B | M | E],
            'qCategory' : [1...],
            'agentNameOrID' : agentName or agentID giving this answer,
            'responseWasSelected': True | False,
            'responseID' : -1 or [1...10],
            'logicengine-name': ...,
            'logicengine-class': ...
        }
    }

NOTE: You MUST return the logicengine-name / -class as you have found them if the
      user has selected from recommended responses!!!
"""
class APIHLIList(Resource):
    def __init__(self):
        self.reqp = reqparse.RequestParser()
        self.reqp.add_argument('hliClientID', type=str, required=True)
        self.reqp.add_argument('agentNameOrID', type=str, required=True)
        super(APIHLIList, self).__init__()

    def post(self):
        global benderCore
        return benderCore.hliList(self.reqp.parse_args())


class APIHLILockItem(Resource):
    def __init__(self):
        self.reqp = reqparse.RequestParser()
        self.reqp.add_argument('hliClientID', type=str, required=True)
        self.reqp.add_argument('requestID', type=str, required=True)
        self.reqp.add_argument('agentNameOrID', type=str, required=True)
        super(APIHLILockItem, self).__init__()

    def post(self):
        global benderCore
        return benderCore.hliLockItem(self.reqp.parse_args())


class APIHLIDeleteItem(Resource):
    def __init__(self):
        self.reqp = reqparse.RequestParser()
        self.reqp.add_argument('hliClientID', type=str, required=True)
        self.reqp.add_argument('requestID', type=str, required=True)
        self.reqp.add_argument('reason', type=int, required=True)
        self.reqp.add_argument('agentNameOrID', type=str, required=True)
        super(APIHLIDeleteItem, self).__init__()

    def delete(self):
        global benderCore
        return benderCore.hliDeleteItem(self.reqp.parse_args())


class APIHLIUnlockLockItem(Resource):
    def __init__(self):
        self.reqp = reqparse.RequestParser()
        self.reqp.add_argument('hliClientID', type=str, required=True)
        self.reqp.add_argument('requestID', type=str, required=True)
        self.reqp.add_argument('agentNameOrID', type=str, required=True)
        super(APIHLIUnlockLockItem, self).__init__()

    def post(self):
        global benderCore
        return benderCore.hliUnlockItem(self.reqp.parse_args())


class APIHLIAnswerItem(Resource):
    def __init__(self):
        self.reqp = reqparse.RequestParser()
        self.reqp.add_argument('hliClientID', type=str, required=True)
        self.reqp.add_argument('requestID', type=str, required=True)
        self.reqp.add_argument('response', type=dict)
        self.reqp.add_argument('agentNameOrID', type=str, required=True)
        super(APIHLIAnswerItem, self).__init__()

    def post(self):
        global benderCore
        return benderCore.hliAnswerItem(self.reqp.parse_args())

"""
Class APIHeartbeat

It is an API class handling the '/heartbeat'-request.
It forwards the request to BenderCore and returns it's response
as a JSON-Structure
The idea here is to get an analysis from BenderCore about its status and respond
with "200" (everything fine, continue with requests) or an error indicating that
BenderCore is "not in a good shape"
"""
class APIHeartbeat(Resource):
    def __init__(self):
        self.reqp = reqparse.RequestParser()
        self.reqp.add_argument('clientID', type=str, required=True)
        super(APIHeartbeat, self).__init__()

    def get(self):
        global benderCore
        if benderCore.clientAllowed(self.reqp.parse_args()):
            return benderCore.heartbeat()
        else:
            return unauthorized()


class APISimpleUI(Resource):
    def __init__(self):
        self.reqp = reqparse.RequestParser()
        super(APISimpleUI, self).__init__()

    def get(self):
        simpleUIFile = "ui/simple-ui.html"
        if os.path.exists(simpleUIFile):
            with open(simpleUIFile, 'r') as f:
                response = make_response(f.read())
                response.headers['content-type'] = "text/html"
                return response
        return {}, 404


class APISimpleHLI(Resource):
    def __init__(self):
        self.reqp = reqparse.RequestParser()
        super(APISimpleHLI, self).__init__()

    def get(self):
        simpleUIFile = "ui/hli/hli.html"
        if os.path.exists(simpleUIFile):
            with open(simpleUIFile, 'r') as f:
                response = make_response(f.read())
                response.headers['content-type'] = "text/html"
                return response
        return {}, 404


def serve_page(file_relative_path_to_root):
    return send_from_directory('ui', file_relative_path_to_root)


# Let's print out some copyright if we are running as a standalone
# Development machine...
if __name__ == '__main__':
    print('' + BENDER_FULL_VERSION +' - Copyright (c) 2019 Imdat Solak')
    print('        Written by: Imdat Solak (imdat@solak.de)')
    print('=========================================================================')
    print('Loading application, please wait...')

benderCore = BenderCore(benderConfig)
app = Flask(__name__)
api = Api(app)
"""
Add the possible API-Endpoints to flask/flask_restful so that the right
classes can respond
"""
api.add_resource(APIBenderConfiguration, API_ROOT + '/configuration')
api.add_resource(APISession, API_ROOT + '/session')
api.add_resource(APIQuery, API_ROOT + '/query')
api.add_resource(APIJob, API_ROOT + '/job')
api.add_resource(APIResponse, API_ROOT + '/response')
api.add_resource(APIReinforcedLearning, API_ROOT + '/reinforce')
api.add_resource(APIHeartbeat, API_ROOT + '/heartbeat')
api.add_resource(APIHLIList, API_ROOT + '/hli/list')
api.add_resource(APIHLILockItem, API_ROOT + '/hli/lock')
api.add_resource(APIHLIDeleteItem, API_ROOT + '/hli/delete')
api.add_resource(APIHLIUnlockLockItem, API_ROOT + '/hli/unlock')
api.add_resource(APIHLIAnswerItem, API_ROOT + '/hli/answer')

"""
If we're running as a standalone application (and cen respond to only one API-call
at the same time), run us in debug-mode with Flask's own server...
"""
if __name__ == '__main__':
    api.add_resource(APISimpleHLI, '/ui/hli/')
    api.add_resource(APISimpleUI, '/ui/')
    app.add_url_rule('/ui/<path:file_relative_path_to_root>', 'serve_page', serve_page, methods=['GET'])

    utils.safe_create_directory(os.path.dirname(accessLogFile))
    logger = logging.getLogger('werkzeug')
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(accessLogFile)
    logger.addHandler(handler)
    logger.propagate = 0
    app.logger.addHandler(handler)

    print("=========================================================================")
    print('   | Starting web-server...')
    print('   | HTTP-Logging to: ', accessLogFile, sep='')
    print('   | Point your browser to : http://', devServerIP, ':', devServerPort, '/ui/', sep='')
    print("=========================================================================")
    app.run(host=devServerIP, port=devServerPort, debug=False)

