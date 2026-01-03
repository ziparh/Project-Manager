#!/usr/bin/env bash

set -e

echo "Start applying migrations..."
uv run alembic upgrade head
echo "Migrations applied"

exec "$@"