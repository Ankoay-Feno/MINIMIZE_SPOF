#!/bin/sh
set -eu

# Render frontend runtime config from environment variables.
envsubst '${API_URL}' \
  < /usr/share/nginx/html/config.js.template \
  > /usr/share/nginx/html/config.js
