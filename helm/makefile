
deploy-helm:
	. ./../src/.env && \
	helm upgrade --install gagarin . --namespace fyodorov --create-namespace \
	--set env.SUPABASE_PROJECT_URL=$${SUPABASE_PROJECT_URL} \
	--set env.SUPABASE_API_KEY=$${SUPABASE_API_KEY} \
	--set env.JWT_SECRET=$${JWT_SECRET}