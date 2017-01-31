# Barebones Apache installation on Ubuntu

FROM ubuntu

MAINTAINER scuq

ENV DEBIAN_FRONTEND noninteractive

# install required debian packages
RUN apt-get update && apt-get -y upgrade
RUN apt-get -y install python python-falcon python-requests python-rrdtool python-pil apache2 libapache2-mod-wsgi

RUN a2enmod wsgi 
RUN a2enmod headers

# install sqensor
RUN mkdir -p /var/www/sqensor
RUN mkdir -p /var/www/sqensor_server 
RUN mkdir -p /var/lib/sqensor/rrds 
RUN mkdir -p /var/lib/sqensor/sensors 
RUN mkdir -p /var/log/sqensor/ 
RUN mkdir /etc/sqensor


ADD sqensor_server/sqensor_server.py /var/www/sqensor_server/sqensor_server.py
ADD sqensor_server/etc /etc/sqensor

RUN chown -R www-data:www-data /var/log/sqensor
RUN chown -R www-data:www-data /var/lib/sqensor
RUN chown -R root:www-data /etc/sqensor


# Update the default apache site with the config we created.
ADD apache-config/000-default.conf /etc/apache2/sites-enabled/000-default.conf
ADD apache-config/security.conf /etc/apache2/conf-available/security.conf

ENV APACHE_RUN_USER www-data
ENV APACHE_RUN_GROUP www-data
ENV APACHE_LOG_DIR /var/log/apache2
ENV APACHE_LOCK_DIR /var/lock/apache2
ENV APACHE_PID_FILE /var/run/apache2.pid

EXPOSE 80


# By default start up apache in the foreground, override with /bin/bash for interative.
CMD /usr/sbin/apache2ctl -D FOREGROUND
