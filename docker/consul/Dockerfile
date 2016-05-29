FROM ubuntu:16.04
MAINTAINER Aurelien Bruno <aurelbruno06@gmail.com>
RUN apt-get update && apt-get install -y unzip
ADD https://releases.hashicorp.com/consul/0.6.4/consul_0.6.4_linux_amd64.zip /tmp/consul_0.6.4_linux_amd64.zip
RUN cd /usr/bin && unzip /tmp/consul_0.6.4_linux_amd64.zip && rm /tmp/consul_0.6.4_linux_amd64.zip
ADD https://releases.hashicorp.com/consul-template/0.14.0/consul-template_0.14.0_linux_amd64.zip /tmp/consul-template_0.14.0_linux_amd64.zip
RUN cd /usr/bin && unzip /tmp/consul-template_0.14.0_linux_amd64.zip && rm /tmp/consul-template_0.14.0_linux_amd64.zip
EXPOSE 8300 8301 8301/udp 8302 8302/udp 8400 8500 53/udp

