FROM alpine:latest
MAINTAINER Aurelien Bruno <aurelbruno@gmail.com>
RUN apk update && apk add nodejs git python && rm -rf /var/cache/apk/*
RUN npm install -g npm@3.x 
RUN npm install -g i18next@3.x
RUN npm install -g node-gyp
RUN npm install -g node-red 
RUN mkdir -p /home/nodered/.node-red/
EXPOSE 1880
WORKDIR /home/nodered/.node-red/
ENTRYPOINT ["/usr/bin/node-red","-v"]

