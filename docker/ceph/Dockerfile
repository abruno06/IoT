FROM ubuntu:16.04
LABEL MAINTAINER="Aurelien Bruno <aurelbruno06@gmail.com>"
#RUN apt-get autoremove && apt-get update && apt-get upgrade -y && apt-get install -y wget  && rm -rf /var/lib/apt/lists/* 
#ADD https://download.ceph.com/keys/release.asc /tmp/release.asc
#RUN apt-key add /tmp/release.asc && echo "deb http://download.ceph.com/debian-jewel/ xenia main" > /etc/apt/sources.list.d/ceph.list && apt-get autoremove && apt-get update 
#RUN apt-key add /tmp/release.asc && echo "deb http://download.ceph.com/debian-jewel/ xenia main" > /etc/apt/sources.list.d/ceph.list
RUN apt-get update && apt-get install -y ceph ceph-deploy ceph-fs-common ceph-mds && rm -rf /var/lib/apt/lists/* 

