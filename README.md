# sqsensor

## Server

Apache Config Example

```
<VirtualHost *:80>

        ServerAdmin webmaster@localhost
        DocumentRoot /var/www/html

        WSGIDaemonProcess www-data python-path=/var/www/sqensor;/var/lib/sqensor/rrds/
        WSGIProcessGroup www-data
        WSGIScriptAlias /sqensor/server /var/www/sqensor_server/sqensor_server.py
        WSGIPassAuthorization On

        ErrorLog ${APACHE_LOG_DIR}/error.log
        CustomLog ${APACHE_LOG_DIR}/access.log combined
</VirtualHost>
```

## Client

````$ sqensor_client.py -n "Living Room" --register ```

````$ sqensor_client.py -a xYzxyz -n "Living Room" -u http://your.server/sqensor/server/```

```

Usage: sqensor_client.py [options]

Options:
  -h, --help            show this help message and exit
  -v, --register        enable verbose output
  -n SENSORNAME, --sensor-name=SENSORNAME
                        sensor name
  -i INTERVAL, --interval=INTERVAL
                        interval in seconds, default 10
  -a AUTHTOKEN, --authtoken=AUTHTOKEN
                        authtoken
  -p ADAFRUITPIN, --adafruit-pin=ADAFRUITPIN
                        adafruit pin, default 4
  -t ADAFRUITSENSORTYPE, --adafruit-sensortype=ADAFRUITSENSORTYPE
                        adafruit sensor type, default Adafruit_DHT.DHT22
  -u SQENSORBASEURL, --sqensor-baseurl=SQENSORBASEURL
                        sqensor base url default http://127.0.0.1:8000

```
