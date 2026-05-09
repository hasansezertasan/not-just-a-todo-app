#!/usr/bin/env sh
set -eu

# Apply database migrations before serving traffic.
flask db upgrade

exec "$@"
