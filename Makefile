.DEFAULT_GOAL := all
PM2_PROJECT = hydroshare
.PHONY: up-landing
up-landing:
	export VITE_APP_BASE=/resource/
	cd landing-page && npx pm2 start npm --name $(PM2_PROJECT) -- run serve

.PHONY: down-landing
down-landing:
	npx pm2 delete $(PM2_PROJECT)

.PHONY: logs-landing
logs-landing:
	npx pm2 logs $(PM2_PROJECT)
