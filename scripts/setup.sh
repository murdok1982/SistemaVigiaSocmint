#!/bin/bash
echo "VIGÍA System Setup"
echo "=================="
if [ ! -f .env ]; then
    echo "Generating .env from .env.example..."
    cp .env.example .env
    echo "Generating random keys..."
    sed -i "s/^POSTGRES_PASSWORD=$/POSTGRES_PASSWORD=$(openssl rand -hex 32)/" .env
    sed -i "s/^REDIS_PASSWORD=$/REDIS_PASSWORD=$(openssl rand -hex 32)/" .env
    sed -i "s/^JWT_SECRET_KEY=$/JWT_SECRET_KEY=$(openssl rand -hex 32)/" .env
    sed -i "s/^VIGIA_MASTER_KEY=$/VIGIA_MASTER_KEY=$(openssl rand -hex 32)/" .env
    sed -i "s/^VIGIA_HMAC_KEY=$/VIGIA_HMAC_KEY=$(openssl rand -hex 32)/" .env
    sed -i "s/^HMAC_SECRET=$/HMAC_SECRET=$(openssl rand -hex 32)/" .env
    sed -i "s/^VIGIA_HASH_SALT=$/VIGIA_HASH_SALT=$(openssl rand -hex 16)/" .env
    sed -i "s/^VIGIA_API_KEY=$/VIGIA_API_KEY=$(openssl rand -hex 32)/" .env
    sed -i "s/^GRAFANA_ADMIN_PASSWORD=$/GRAFANA_ADMIN_PASSWORD=$(openssl rand -hex 16)/" .env
    echo ".env generated. Review and adjust as needed."
else
    echo ".env already exists. Skipping generation."
fi
echo "Setup complete. Run: docker-compose up -d"
