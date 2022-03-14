FROM aurelbruno06/node_red_base_alpine:latest
LABEL MAINTAINER="Aurelien Bruno <aurelbruno06@gmail.com>"
RUN npm install -g node-red-node-sqlite node-red-contrib-cassandra node-red-contrib-amqp aes-js mimelib node-red-node-base64 
COPY ./static-settings.js /root/.node-red/settings.js
EXPOSE 1880
WORKDIR /home/nodered/.node-red/
ENTRYPOINT ["/usr/bin/node-red","-v"]

