#!/bin/bash
set -e

REMOTE_HOST="hetzner"
REMOTE_PATH="~/news"
PROJECT_NAME="news-embedding-filter"

echo "🚀 Deploying News Embedding Filter Service to Hetzner..."

# Test SSH connection
if ! ssh "$REMOTE_HOST" "echo 'Connection test'"; then
    echo "❌ SSH connection failed"
    exit 1
fi

echo "✅ SSH connection successful"

# Sync project files
echo "📦 Syncing project files..."
rsync -avz --delete \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='*.log' \
    --exclude='data/' \
    --exclude='.python-version' \
    --exclude='uv.lock' \
    embedding_service.py \
    filter_logic.py \
    Dockerfile.embedding \
    docker-compose.embedding.yml \
    requirements.txt \
    $REMOTE_HOST:$REMOTE_PATH/

echo "✅ Files synced"

# Remote build and deploy
echo "🐳 Building and deploying container..."
ssh $REMOTE_HOST "cd $REMOTE_PATH && \
    docker network create quietloop-network 2>/dev/null || true && \
    docker compose -f docker-compose.embedding.yml down || true && \
    docker compose -f docker-compose.embedding.yml up -d --build"

echo "⏳ Waiting for service to be healthy..."
sleep 5

# Check health
if ssh $REMOTE_HOST "curl -f http://localhost:3007/health" &>/dev/null; then
    echo "✅ Service is healthy!"
else
    echo "⚠️  Service might still be starting, check logs with:"
    echo "   ssh $REMOTE_HOST 'docker logs news-embedding-filter'"
fi

echo ""
echo "✅ Deployment complete!"
echo "🔗 Internal URL: http://localhost:3007 (on Hetzner)"
echo "📋 Health: curl http://localhost:3007/health"
echo ""
echo "📝 Next steps:"
echo "1. Test the service on Hetzner"
echo "2. Add Caddy routing if public access needed (currently internal only)"
echo "3. Update GitHub Actions to use this service"
