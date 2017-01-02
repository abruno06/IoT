FROM resin/rpi-raspbian:jessie
MAINTAINER Aurelien Bruno <aurelbruno06@gmail.com>
RUN gpg --keyserver hkp://subkeys.pgp.net --recv-keys 82B129927FA3303E
RUN echo "deb http://archive.raspberrypi.org/debian/ jessie main ui" > /etc/apt/sources.list.d/raspi.list
RUN apt-get --allow-unauthenticated update && apt-get install -y nodered npm
RUN npm config set strict-ssl false
RUN npm install --global node-red-node-email node-red-contrib-soap node-red-dashboard
COPY ./static.js /root/.node-red/settings.js
EXPOSE 1880
ENTRYPOINT ["/usr/bin/node-red"]
