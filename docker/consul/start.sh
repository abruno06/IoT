#!/bin/bash
/usr/bin/consul agent -server -bootstrap-expect 3 -data-dir /tmp/consul -config-dir /etc/consul.d &
sleep 30
/usr/bin/consul join consul1 consul2 consul3 
/bin/true
