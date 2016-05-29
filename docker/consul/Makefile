build: 
	docker build -t aurelbruno06/consul_base .
build-srv:
	docker build -f Dockerfile.server -t aurelbruno06/consul_server .
build-client:
	docker build -f Dockerfile.client -t aurelbruno06/consul_client .
export:
	docker push aurelbruno06/consul_base
