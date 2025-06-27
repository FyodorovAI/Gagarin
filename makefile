
docker-build:
	docker build -t gagarin:main .

push-docker:
	docker push gagarin:main