FROM docker.io/transloadit/companion:6.0.0

RUN mv /app/lib/config/companion.js /app/lib/config/default-config.js

COPY companion-custom-config.js /app/lib/config/companion.js

RUN mv /app/lib/server/helpers/utils.js /app/lib/server/helpers/default-utils.js

COPY companion-custom-utils.js /app/lib/server/helpers/utils.js

RUN mv /app/lib/server/s3-client.js /app/lib/server/default-s3-client.js

COPY companion-custom-s3-client.js /app/lib/server/s3-client.js

RUN mv /app/lib/server/middlewares.js /app/lib/server/default-middlewares.js

COPY companion-custom-middlewares.js /app/lib/server/middlewares.js