
docker-build:
	docker build -t gagarin:main .

push-docker:
	docker push gagarin:main

helm-deploy:
	. ./src/.env && \
	helm upgrade --install gagarin ./helm --namespace fyodorov --create-namespace --dry-run \
	--set env.SUPABASE_PROJECT_URL=$${SUPABASE_PROJECT_URL} \
	--set env.SUPABASE_API_KEY=$${SUPABASE_API_KEY} \
	--set env.JWT_SECRET=$${JWT_SECRET}