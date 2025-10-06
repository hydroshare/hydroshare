.DEFAULT_GOAL := all
DISCOVER_CONTAINER = discovery-atlas
.PHONY: up-front
up-front:
	export VITE_APP_BASE=/search/
	cd discovery-atlas/frontend && npx pm2 start npm --name $(DISCOVER_CONTAINER) -- run serve

.PHONY: down-front
down-front:
	npx pm2 delete $(DISCOVER_CONTAINER)

.PHONY: logs-front
logs-front:
	npx pm2 logs $(DISCOVER_CONTAINER)
