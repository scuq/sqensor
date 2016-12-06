#!/usr/bin/env /usr/bin/python
# -*- coding: utf-8 -*-
me = "sqensor_client"

import Adafruit_DHT
import json
import time
import datetime
import sys
import requests
from optparse import OptionParser
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


def main():

	parser = OptionParser()
	parser.add_option("-v", "--register", action="store_true", dest="register", default=False, help="enable verbose output")
	parser.add_option("-n", "--sensor-name", dest="sensorname", help="sensor name")
	parser.add_option("-i", "--interval", dest="interval", help="interval in seconds, default 10")
	parser.add_option("-a", "--authtoken", dest="authtoken", help="authtoken")
	parser.add_option("-p", "--adafruit-pin", dest="adafruitpin", help="adafruit pin, default 4")
	parser.add_option("-t", "--adafruit-sensortype", dest="adafruitsensortype", help="adafruit sensor type, default Adafruit_DHT.DHT22")
	parser.add_option("-u", "--sqensor-baseurl", dest="sqensorbaseurl", help="sqensor base url default http://127.0.0.1:8000")

	(options, args) = parser.parse_args()

	pin = 4
	interval = 10
	sensorname = ""
	authtoken = ""
	adafruitsensortype = Adafruit_DHT.DHT22
	sqensor_url = "http://127.0.0.1:8000"

	if options.sqensorbaseurl:
		sqensor_url = options.sqensorbaseurl

	if options.adafruitpin:
		pin = options.adafruitpin

	if options.adafruitsensortype:
		if options.adafruitsensortype == "Adafruit_DHT.DHT22":
			adafruitsensortype  = Adafruit_DHT.DHT22
		
	if not options.authtoken:
		print "specify an authtoken"
		sys.exit(1)
	else:
		authtoken = options.authtoken

	if options.interval:
		interval = options.interval

	if options.sensorname:
		sensorname = options.sensorname

	else:
		print "specify a sensor name"
		sys.exit(1)

	headers={"content-type":"application/json", "Authorization":""+authtoken+"" }

	if options.register:
		print "registering new sensor to sqensor."

		register_payload = {'name': ''+sensorname+'', 'type': 'dht22'}

		r = requests.post(sqensor_url+"/register", data=json.dumps(register_payload), headers=headers)

		print r.text
		print r.status_code

	else:
		while True:

			if adafruitsensortype  == Adafruit_DHT.DHT22:
				humidity, temperature = Adafruit_DHT.read_retry(adafruitsensortype, pin)
				datalog_payload = {'name': ''+sensorname+'', 'type': 'dht22', 'data': [str(temperature),str(humidity)] }

			try:
				r = requests.post(sqensor_url+"/data", data=json.dumps(datalog_payload), headers=headers)
				print r.text
				print r.status_code
				logger.info(r.status_code)
				time.sleep(interval)
			except requests.exceptions.ConnectionError:
				logger.error(str(sys.exc_info()[0])+" "+str(sys.exc_info()[1]))
				time.sleep(interval*3)
				
				


if __name__=='__main__': main()
