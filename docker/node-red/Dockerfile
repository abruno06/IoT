FROM ubuntu:16.04
MAINTAINER Aurelien Bruno (aurelbruno06@gmail.com)
# This Docker container is just building a simple node-red (v4) container above ubuntu
RUN apt-get autoremove && apt-get update && apt-get upgrade -y && apt-get install -y curl git npm && curl -sL https://deb.nodesource.com/setup_4.x | bash - && apt-get install -y nodejs && rm -rf /var/lib/apt/lists/*
RUN npm install -g i18next node-red
RUN mkdir -p /home/nodered/.node-red/
COPY ./static-settings.js /root/.node-red/settings.js
EXPOSE 1880
ENTRYPOINT ["/usr/bin/node-red"]

