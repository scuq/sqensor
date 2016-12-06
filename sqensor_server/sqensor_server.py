#!/usr/bin/env /usr/bin/python
# -*- coding: utf-8 -*-
me = "sqensor_server"
import json
import logging
import uuid
from wsgiref import simple_server
import os
import falcon
import requests
import sys
import rrdtool

import logging

if not sys.platform == "win32":
        from logging.handlers import SysLogHandler

logger = logging.getLogger(__name__)
formatter = logging.Formatter('%(asctime)s %(levelname)s '+me+' %(message)s')


if sys.platform == 'win32':
        hdlr = logging.FileHandler(os.path.normpath(os.environ["USERPROFILE"]+os.sep+__name__+".log"))
        hdlr.setFormatter(formatter)
        logger.addHandler(hdlr)

else:
        syslog = SysLogHandler(address='/dev/log',facility="local5")
        syslog.setFormatter(formatter)
        logger.addHandler(syslog)

logger.setLevel(logging.INFO)

configfile = "/etc/sqensor/config.json"

storageroot=None
sensorregister=None
validtokens=[]
rrddir=None
wwwrootdir=None
config = None


if os.path.isfile(configfile):
	with open(configfile) as data_file:    
		config = json.load(data_file)
		storageroot=config["storageRootDir"]		
		sensorregister=config["sensorRegisterDir"]
		rrddir=config["rrdDir"]
		wwwrootdir=config["wwwrootDir"]
		validtokens=config["authorizedTokens"]
		
if not config:
	sys.exit(1)

if not os.path.isdir(sensorregister):
	os.makedirs(sensorregister)	

if not os.path.isdir(rrddir):
	os.makedirs(rrddir)	

if not os.path.isdir(wwwrootdir):
	os.makedirs(wwwrootdir)	




class StorageEngine(object):

    def createRrd(self,filename,sensortype):

        sensortypefound = False

	print sensortype

        if sensortype == "DHT11" or sensortype == "DHT22":

                sensortypefound = True

                rrdtool.create(str(filename),
                           '--step', '30s',
                           '--start', 'now-1h',
                           'DS:temperature:GAUGE:120s:-60:80',
                           'DS:humidity:GAUGE:120s:-60:80',
                           'RRA:MIN:0.5:1:2880',
                           'RRA:MAX:0.5:1:2800',
                           'RRA:AVERAGE:0.5:1:2880',
                )


        if sensortypefound == False:
                raise falcon.HTTPError(falcon.HTTP_727,
                        'Register Error',
                        'Unknown type of sensor, valid types: DHT11, DHT22')

    def graphRrd(self,pngfilename,rrdfilename,sensortype,sensordata):

        if sensortype == "DHT11" or sensortype == "DHT22":
		rrdtool.graph(str(pngfilename),
                                                   '--imgformat', 'PNG',
                                                   '--width', '1121',
                                                   '--height', '313',
                                                   '--start', "now-1h",
                                                   '--end', "-1",
                                                   '--vertical-label', 'value',
                                                   '--title', str(sensortype)+' Sensor',
                                                   '--lower-limit', '-30',
                                                   '--upper-limit', '50',
                                                   'DEF:temperature='+str(rrdfilename)+':temperature:MAX',
                                                   'DEF:humidity='+str(rrdfilename)+':humidity:MAX',
                                                   'LINE:temperature#9E3C97:temperature',
                                                   'LINE:humidity#1D329B:humidity',
                                                   'HRULE:0#FF6A00',
                                                   'HRULE:23#FF0000',
                                                   'GPRINT:temperature:LAST:Current\:%8.5lf',
                                                   'GPRINT:temperature:AVERAGE:Average\:%8.5lf',
                                                   'GPRINT:temperature:MAX:Maximum\:%8.5lf'
						)

    def updateRrd(self,filename,sensortype,sensordata):

        sensortypefound = False

        if sensortype == "DHT11" or sensortype == "DHT22":

        	sensortypefound = True
		rrdtool.update(str(filename), 'N:'+str(sensordata[0])+":"+str(sensordata[1]))

		

        if sensortypefound == False:
                raise falcon.HTTPError(falcon.HTTP_727,
                        'Data Logger Error',
                        'Unknown type of sensor, valid types: DHT11, DHT22')

    def register(self,sensor):
	try:
		sensorname = sensor["name"]
		sensortype = str(sensor["type"]).upper()
	except:
		raise falcon.HTTPError(falcon.HTTP_727,
			'Register Error',
			str(sys.exc_info()[0])+" "+str(sys.exc_info()[1]))

	if os.path.isfile(sensorregister+os.sep+sensorname):
   		raise falcon.HTTPError(falcon.HTTP_726,
                               'Register Error',
                               'Sensor with this Name already registered')
	else:
		open(sensorregister+os.sep+sensorname,'w').close() 

		_rrdfile = rrddir+os.sep+sensorname+".rrd"


		self.createRrd(_rrdfile,sensortype)

		

	return sensor["name"]


    def get_last(self, id):
	retrun [{'id': str(uuid.uuid4()), 'data': 9}]	

    def get_measureddata(self, marker, limit):
	return

    def add_measureddata(self, sensor):
        try:
                sensorname = sensor["name"]
                sensortype = str(sensor["type"]).upper()
                sensordata = sensor["data"]
	except:
                raise falcon.HTTPError(falcon.HTTP_727,
                        'Data Logger Error',
                        str(sys.exc_info()[0])+" "+str(sys.exc_info()[1]))

	if not type(sensordata) == list:
		                raise falcon.HTTPError(falcon.HTTP_727,
       		                        'Value Error',
       		                        'Data have to be an array')
  	
        if not os.path.isfile(sensorregister+os.sep+sensorname):
                raise falcon.HTTPError(falcon.HTTP_726,
                               'Register Error',
                               'No Sensor with this Name registered')

	else:

		_rrdfile = rrddir+os.sep+sensorname+".rrd"
		_pngfile = wwwrootdir+os.sep+sensorname+".png"

		self.updateRrd(_rrdfile,sensortype,sensordata)
		self.graphRrd(_pngfile,_rrdfile,sensortype,sensordata)

        return sensordata



class StorageError(Exception):

    @staticmethod
    def handle(ex, req, resp, params):
        description = ('Sorry, couldn\'t write your data to the '
                       'rrd file.')

        raise falcon.HTTPError(falcon.HTTP_725,
                               'Database Error',
                               description)



class AuthMiddleware(object):

    def process_request(self, req, resp):
        token = req.get_header('Authorization')
        account_id = req.get_header('Account-ID')

        challenges = ['Token type="Sqensor"']

        if token is None:
            description = ('Please provide an auth token '
                           'as part of the request.')

            raise falcon.HTTPUnauthorized('Auth token required',
                                          description,
                                          challenges,
                                          href='https://www.github.com/scuq/sqensor')

        if not self._token_is_valid(token, account_id):
            description = ('The provided auth token is not valid. '
                           'Please request a new token and try again.')

            raise falcon.HTTPUnauthorized('Authentication required',
                                          description,
                                          challenges,
                                          href='https://www.github.com/scuq/sqensor')

    def _token_is_valid(self, token, account_id):
	for t in validtokens:
		if t == token:
			return True
	return False


class RequireJSON(object):

    def process_request(self, req, resp):
        if not req.client_accepts_json:
            raise falcon.HTTPNotAcceptable(
                'This API only supports responses encoded as JSON.',
                href='https://www.github.com/scuq/sqensor')

        if req.method in ('POST', 'PUT'):
            if 'application/json' not in req.content_type:
                raise falcon.HTTPUnsupportedMediaType(
                    'This API only supports requests encoded as JSON.',
                    href='https://www.github.com/scuq/sqensor')


class JSONTranslator(object):

    def process_request(self, req, resp):
        # req.stream corresponds to the WSGI wsgi.input environ variable,
        # and allows you to read bytes from the request body.
        #
        # See also: PEP 3333
        if req.content_length in (None, 0):
            # Nothing to do
            return

        body = req.stream.read()
        if not body:
            raise falcon.HTTPBadRequest('Empty request body',
                                        'A valid JSON document is required.')

        try:
            req.context['doc'] = json.loads(body.decode('utf-8'))

        except (ValueError, UnicodeDecodeError):
            raise falcon.HTTPError(falcon.HTTP_753,
                                   'Malformed JSON',
                                   'Could not decode the request body. The '
                                   'JSON was incorrect or not encoded as '
                                   'UTF-8.')

    def process_response(self, req, resp, resource):
        if 'result' not in req.context:
            return

        resp.body = json.dumps(req.context['result'])


def max_body(limit):

    def hook(req, resp, resource, params):
        length = req.content_length
        if length is not None and length > limit:
            msg = ('The size of the request is too large. The body must not '
                   'exceed ' + str(limit) + ' bytes in length.')

            raise falcon.HTTPRequestEntityTooLarge(
                'Request body is too large', msg)

    return hook

class SensorRegister(object):

    def __init__(self, db):
        self.db = db
        self.logger = logging.getLogger('SensorRegister.' + __name__)
	
    @falcon.before(max_body(64 * 1024))
    def on_post(self, req, resp):
        try:
            doc = req.context['doc']
        except KeyError:
            raise falcon.HTTPBadRequest(
                'Missing Sensor Data',
                'Data must be submitted in the request body.')

        registered_sensor = self.db.register(doc)


        resp.status = falcon.HTTP_201
        resp.location = '/register/%s' % (str(registered_sensor))

class DataResource(object):

    def __init__(self, db):
        self.db = db
        self.logger = logging.getLogger('Dataresource.' + __name__)

    @falcon.before(max_body(64 * 1024))
    def on_post(self, req, resp):
	logger.info("received new data from"+str(req))
        try:
            doc = req.context['doc']
        except KeyError:
            raise falcon.HTTPBadRequest(
                'Missing Data',
                'MeasuredData be submitted in the request body.')

        proper_data = self.db.add_measureddata(doc)

        resp.status = falcon.HTTP_201
        resp.location = '/data/%s' % (proper_data)


# Configure your WSGI server to load "things.app" (app is a WSGI callable)
application = falcon.API(middleware=[
    AuthMiddleware(),
    RequireJSON(),
    JSONTranslator(),
])

db = StorageEngine()
data = DataResource(db)
register = SensorRegister(db)
application.add_route('/data', data)
application.add_route('/register', register)

# If a responder ever raised an instance of StorageError, pass control to
# the given handler.
application.add_error_handler(StorageError, StorageError.handle)

	

def main(): 

    logger.info("starting httpd")
    #httpd = simple_server.make_server('0.0.0.0', 8000, app)
    #httpd.serve_forever()

if __name__=='__main__': main()
