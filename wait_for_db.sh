#!/bin/sh

set -e

host="db"
port="5432"

echo "⏳ Esperando a que PostgreSQL ($host:$port) esté disponible..."

until nc -z "$host" "$port"; do
  sleep 1
done

echo "✅ PostgreSQL está listo. Continuando..."
exec "$@"
