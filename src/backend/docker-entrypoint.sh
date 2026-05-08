#!/bin/sh
set -e

echo "=== Running database migrations ==="
cd /app/db && alembic upgrade head
echo "=== Migrations complete ==="

# 切回 /app 以便正确加载 app 模块
cd /app

exec "$@"
