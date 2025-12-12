# HydroShare Discovery Portal with Atlas

## Getting Started

### API for local development
```console
# modify settings as necessary in the [main .env](./.env) (at least MONGO_URL and MONGO_DATABASE)
make build
make up
```
The root route of the API will be available at http://localhost:8000. 
The swagger docs will be at http://localhost:8000/docs. 
The Redoc is at http://localhost:8000/redoc. 

### Frontend for local development

The [frontend .env](frontend/.env.development) is commited according to the [Vite standards](https://vite.dev/guide/env-and-mode#env-variables-and-modes). We recommend that you create a separate `frontend/.env.local` file and add any modifications you would like. If you're not running the API locally, you will want to add an entry in your local env for [VITE_APP_API_URL](https://github.com/hydroshare/hydroshare/blob/5726/devincowan/discovery-ui-keep-solr/discovery-atlas/frontend/.env.development#L5).

Then run the Vue app in the background (hmr enabled) using [PM2](https://pm2.io/) via the [Makefile](../Makefile):
```console
make up-discover
npx pm2 ls #(optionally, to list all pm2 services)
make logs-discover #(optionally to tail logs)
```


Or if you prefer, you can run the app using npm:
```console
cd frontend
npm install
npm run serve
```
Either way, the frontend will be available at http://localhost:5004/
More detailed info is available in the [frontend readme](frontend/README.md)

## Formatting
```console
make format
```
