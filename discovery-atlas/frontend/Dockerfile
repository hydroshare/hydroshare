FROM node:24.3.0 AS node_build

WORKDIR /app
COPY package.json .
COPY package-lock.json .

RUN npm install
COPY . .
RUN npm run build-prod

# Production layer
FROM caddy:2.7.6-alpine AS prod

RUN apk add --no-cache bash

COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Copy config template
COPY Caddyfile.template /etc/caddy/Caddyfile.template

# Copy source dist
COPY --from=node_build /app/dist /srv/discover-frontend

EXPOSE 80

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["caddy", "run", "--config", "/etc/caddy/Caddyfile", "--adapter", "caddyfile"]
