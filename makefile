
docker-build:
	docker build -t gagarin:main .

push-docker:
	docker push gagarin:main

deploy-helm:
	make -C ./helm deploy-helm