#!/bin/sh
set -e

echo "=== Running database migrations ==="
alembic -c db/alembic.ini upgrade head
echo "=== Migrations complete ==="

exec "$@"
