.DEFAULT_GOAL := all
PM2_PROJECT = discovery-atlas

.PHONY: generate-resource-edit-schema-json
generate-resource-edit-schema-json:
	docker exec -w /hydroshare hydroshare python hs_cloudnative_schemas/schema/scripts/generate_resource_edit_schema_json.py

.PHONY: up-discover
up-discover:
	export VITE_APP_BASE=/discover/
	cd discovery-atlas/frontend && npx pm2 start npm --name $(PM2_PROJECT) -- run serve

.PHONY: down-discover
down-discover:
	npx pm2 delete $(PM2_PROJECT)

.PHONY: logs-discover
logs-discover:
	npx pm2 logs $(PM2_PROJECT)
