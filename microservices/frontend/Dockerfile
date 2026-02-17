FROM nginx:stable-alpine

WORKDIR /usr/share/nginx/html

COPY index.html ./index.html
COPY app.js ./app.js
COPY style.css ./style.css
COPY config.js.template ./config.js.template
COPY 30-env-config.sh /docker-entrypoint.d/30-env-config.sh
RUN chmod +x /docker-entrypoint.d/30-env-config.sh

EXPOSE 80
