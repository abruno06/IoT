FROM resin/rpi-raspbian:jessie
MAINTAINER Aurelien Bruno <aurelbruno06@gmail.com>
RUN gpg --keyserver hkp://subkeys.pgp.net --recv-keys 82B129927FA3303E | apt-key add -
RUN echo "deb http://archive.raspberrypi.org/debian/ jessie main ui" > /etc/apt/sources.list.d/raspi.list
RUN apt-get --allow-unauthenticated update && apt-get install nodered && rm -rf /var/lib/apt/lists/*
EXPOSE 1880
ENTRYPOINT ["/usr/bin/node-red"]
