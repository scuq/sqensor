#!/usr/bin/env /usr/bin/python
# -*- coding: utf-8 -*-
me = "sqensor_server"
import json
import logging
import uuid
from optparse import OptionParser
from wsgiref import simple_server
import os
import falcon
import requests
import sys
import rrdtool
from os import walk
import logging
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from PIL import ImageEnhance
import datetime


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

    def generateIndex(self,sensorname):

		f = open(indextemplate, 'r')
		templatehtml = f.readlines()
		f.close()

		widgethtml = ""
		graphhtml = ""

		widgethtml += "<table>"
                for (dirpath, dirnames, filenames) in walk(sensorregister):

                        for sensorname in filenames:

				widgethtml += "<tr>"
                                widgethtml += "<td width=\"200px\"><b>"+sensorname+"</b></td><td><img src=\"%s_last.png\" alt=\"Here should be the Graph for - %s\"/></td>"  % (sensorname, sensorname)
				widgethtml += "</tr>"
		widgethtml += "</table>"

		for (dirpath, dirnames, filenames) in walk(sensorregister):
	
			for sensorname in filenames:

				graphhtml += "<div  align=\"center\"><b>"+sensorname+"</b></div>"  
				graphhtml += "<img src=\"%s_1h.png\" alt=\"Here should be the Graph for - %s\" class=\"floating_element\"/>" % (sensorname, sensorname)
				graphhtml += "<img src=\"%s_24h.png\" alt=\"Here should be the Graph for - %s\" class=\"floating_element\"/>" % (sensorname, sensorname)

		
		templatehtml = "".join(templatehtml).replace("%WIDGETS%",widgethtml)
		templatehtml = "".join(templatehtml).replace("%GRAPH%",graphhtml)

		f = open(wwwrootdir+os.sep+"index.html", 'w')
		f.write(templatehtml)
		f.close()


    def graphLast(self,rrdfilename,sensortype,sensordata,sensorname):
	
	lastpngfilename = wwwrootdir+os.sep+sensorname+"_last.png"	

	if sensortype == "DHT11" or sensortype == "DHT22":

		print rrdtool.fetch(str(rrdfilename),"LAST","now-1m","now-30s")[2][0][0]

		
		font_datetime = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",18)
		font_temperature = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",23)

		
		img = Image.open(widget1template)
		draw = ImageDraw.Draw(img)

		text_datetime = unicode(datetime.datetime.now().strftime('%H:%M'))
		text_temperature = unicode(round(float(rrdtool.fetch(str(rrdfilename),"LAST","now-1m","now-30s")[2][0][0]),1))+u"°C"	

		text_datetime_x, text_datetime_y = font_datetime.getsize(text_datetime)
		text_temperature_x, text_temperature_y = font_temperature.getsize(text_temperature)

		text_datetime_y = text_datetime_y + 50

		x_datetime = (img.width - text_datetime_x)/2
		y_datetime = (img.height - text_datetime_y)/2

		x_temperature = (img.width - text_temperature_x)/2
		y_temperature = (img.height - text_temperature_y)/2

		draw.text ((x_datetime,y_datetime), text_datetime, font=font_datetime)
		draw.text ((x_temperature,y_temperature), text_temperature, font=font_temperature)
		img.save(lastpngfilename,'png')




    def graphRrd(self,rrdfilename,sensortype,sensordata,sensorname):

	pngfilename_24h = wwwrootdir+os.sep+sensorname+"_24h.png"
	pngfilename_1h = wwwrootdir+os.sep+sensorname+"_1h.png"

        if sensortype == "DHT11" or sensortype == "DHT22":
		rrdtool.graph(str(pngfilename_24h),
                                                   '--imgformat', 'PNG',
                                                   '--color', 'CANVAS#000000',
                                                   '--color', 'BACK#000000',
                                                   '--color', 'FONT#FFFFFF',
                                                   '--width', '1121',
                                                   '--height', '313',
                                                   '--start', "now-23h",
                                                   '--end', "-1",
                                                   '--vertical-label', 'value',
                                                   '--title', 'Last 24h: '+ str(sensorname) + ' - Sensor ('+str(sensortype)+')',
                                                   '--lower-limit', '-30',
                                                   '--upper-limit', '50',
                                                   'DEF:temperature='+str(rrdfilename)+':temperature:MAX',
                                                   'DEF:humidity='+str(rrdfilename)+':humidity:MAX',
                                                   'AREA:humidity#1D329B:humidity',
                                                   'LINE3:temperature#FF3700:temperature',
                                                   'HRULE:0#A1F229',
                                                   'GPRINT:temperature:LAST:Current\:%8.5lf',
                                                   'GPRINT:temperature:AVERAGE:Average\:%8.5lf',
                                                   'GPRINT:temperature:MAX:Maximum\:%8.5lf'
						)

                rrdtool.graph(str(pngfilename_1h),
                                                   '--imgformat', 'PNG',
                                                   '--color', 'CANVAS#000000',
                                                   '--color', 'BACK#000000',
                                                   '--color', 'FONT#FFFFFF',
                                                   '--width', '1121',
                                                   '--height', '313',
                                                   '--start', "now-1h",
                                                   '--end', "-1",
                                                   '--vertical-label', 'value',
                                                   '--title', 'Last 1h: ' + str(sensorname) + ' - Sensor ('+str(sensortype)+')',
                                                   '--lower-limit', '-30',
                                                   '--upper-limit', '50',
                                                   'DEF:temperature='+str(rrdfilename)+':temperature:MAX',
                                                   'DEF:humidity='+str(rrdfilename)+':humidity:MAX',
                                                   'AREA:humidity#1D329B:humidity',
                                                   'LINE3:temperature#FF3700:temperature',
                                                   'HRULE:0#A1F229',
                                                   'GPRINT:temperature:LAST:Current\:%8.5lf',
                                                   'GPRINT:temperature:AVERAGE:Average\:%8.5lf',
                                                   'GPRINT:temperature:MAX:Maximum\:%8.5lf'
                                                )

		self.generateIndex(sensorname)

		

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

		self.updateRrd(_rrdfile,sensortype,sensordata)
		self.graphRrd(_rrdfile,sensortype,sensordata,sensorname)
		self.graphLast(_rrdfile,sensortype,sensordata,sensorname)

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


## main

configfile = "/etc/sqensor/config.json"
indextemplate = "/etc/sqensor/index.template"
widget1template = "/etc/sqensor/widget1.png"

storageroot=None
sensorregister=None
validtokens=[]
rrddir=None
wwwrootdir=None
config = None
wwwuser = None
wwwgroup = None

if os.path.isfile(configfile):
        with open(configfile) as data_file:
                config = json.load(data_file)
                storageroot=config["storageRootDir"]
                sensorregister=config["sensorRegisterDir"]
                rrddir=config["rrdDir"]
                wwwrootdir=config["wwwrootDir"]
                validtokens=config["authorizedTokens"]
                wwwuser=config["wwwuser"]
                wwwgroup=config["wwwgroup"]

if not config:
	print "no config loaded."
        sys.exit(1)


def recurseChown(path,uid,gid):

	for root, dirs, files in os.walk(path):  
	  for momo in dirs:  
	    os.chown(os.path.join(root, momo), uid, gid)
	  for momo in files:
	    os.chown(os.path.join(root, momo), uid, gid)

def main(): 

	parser = OptionParser()
	parser.add_option("", "--setup", action="store_true", dest="setup", default=False, help="setup dirs and permissions")
	(options, args) = parser.parse_args()

	if options.setup:

		import pwd

		wwwuid = pwd.getpwnam(wwwuser)[2]
		wwwgid = pwd.getpwnam(wwwgroup)[2]

		print "starting setup"

		if not os.path.isdir(sensorregister):
			print "creating sensorregister direcotry "+sensorregister
       			os.makedirs(sensorregister)

		print "chown of sensorregister direcotry "+sensorregister+" to "+wwwuser+":"+wwwgroup
		recurseChown(sensorregister,wwwuid,wwwgid)

		if not os.path.isdir(rrddir):
			print "creating rrd direcotry "+rrddir
       		 	os.makedirs(rrddir)

		print "chown of rrd direcotry "+sensorregister+" to "+wwwuser+":"+wwwgroup
		recurseChown(rrddir,wwwuid,wwwgid)

		if not os.path.isdir(wwwrootdir):
			print "creating wwwroot direcotry "+wwwrootdir
       		 	os.makedirs(wwwrootdir)

		print "chown of wwwroot direcotry "+sensorregister+" to "+wwwuser+":"+wwwgroup
		recurseChown(wwwrootdir,wwwuid,wwwgid)

		print """example apache2 config:
		<VirtualHost *:80>

		        ServerAdmin webmaster@localhost
		        DocumentRoot /var/www/html

		        WSGIDaemonProcess """+wwwuser+""" python-path=/var/www/sqensor;/var/lib/sqensor/rrds/
		        WSGIProcessGroup """+wwwgroup+"""
		        WSGIScriptAlias /sqensor/server /var/www/sqensor_server/sqensor_server.py
		        WSGIPassAuthorization On

		        ErrorLog ${APACHE_LOG_DIR}/error.log
		        CustomLog ${APACHE_LOG_DIR}/access.log combined
		</VirtualHost>
		"""

		

		sys.exit(0)


	sys.exit(1)

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




if __name__=='__main__': main()
