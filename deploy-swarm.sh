#!/bin/bash

# UnityAI Docker Swarm Deployment Script
# This script deploys the UnityAI stack to Docker Swarm

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
STACK_NAME="unityai"
CONFIG_DIR="./config"
ENV_FILE="$CONFIG_DIR/.env.production"
COMPOSE_FILE="docker-compose.swarm.yml"
SECRETS_DIR="./secrets"

echo -e "${BLUE}=== UnityAI Docker Swarm Deployment ===${NC}"

# Check if running on swarm manager
if ! docker info --format '{{.Swarm.LocalNodeState}}' | grep -q "active"; then
    echo -e "${RED}Error: This node is not part of a Docker Swarm or not a manager node${NC}"
    echo "Please initialize swarm with: docker swarm init"
    exit 1
fi

# Check if .env.production exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: $ENV_FILE not found${NC}"
    echo "Please create the production environment file first"
    exit 1
fi

# Check if docker-compose.swarm.yml exists
if [ ! -f "$COMPOSE_FILE" ]; then
    echo -e "${RED}Error: $COMPOSE_FILE not found${NC}"
    exit 1
fi

# Create secrets directory if it doesn't exist
mkdir -p "$SECRETS_DIR"

echo -e "${YELLOW}Creating Docker secrets...${NC}"

# Function to create secret if it doesn't exist
create_secret() {
    local secret_name=$1
    local secret_file=$2
    
    if docker secret ls --format "{{.Name}}" | grep -q "^${secret_name}$"; then
        echo -e "${YELLOW}Secret $secret_name already exists, skipping...${NC}"
    else
        if [ -f "$secret_file" ]; then
            docker secret create "$secret_name" "$secret_file"
            echo -e "${GREEN}Created secret: $secret_name${NC}"
        else
            echo -e "${RED}Warning: Secret file $secret_file not found for $secret_name${NC}"
            echo -e "${YELLOW}Creating placeholder secret. Please update it manually.${NC}"
            echo "PLACEHOLDER_VALUE" | docker secret create "$secret_name" -
        fi
    fi
}

# Create all required secrets
create_secret "pg_pw" "$SECRETS_DIR/postgres_password.txt"
create_secret "redis_pw" "$SECRETS_DIR/redis_password.txt"
create_secret "n8n_admin_password" "$SECRETS_DIR/n8n_admin_password.txt"
create_secret "n8n_encryption_key" "$SECRETS_DIR/n8n_encryption_key.txt"
create_secret "n8n_api_key" "$SECRETS_DIR/n8n_api_key.txt"
create_secret "cloudflare_email" "$SECRETS_DIR/cloudflare_email.txt"
create_secret "cloudflare_token" "$SECRETS_DIR/cloudflare_token.txt"
create_secret "openai_api_key" "$SECRETS_DIR/openai_api_key.txt"
create_secret "anthropic_api_key" "$SECRETS_DIR/anthropic_api_key.txt"
create_secret "groq_api_key" "$SECRETS_DIR/groq_api_key.txt"
create_secret "grafana_admin_password" "$SECRETS_DIR/grafana_admin_password.txt"
create_secret "runner_token" "$SECRETS_DIR/runner_token.txt"

echo -e "${YELLOW}Deploying stack to Docker Swarm...${NC}"

# Deploy the stack
docker stack deploy -c "$COMPOSE_FILE" "$STACK_NAME"

echo -e "${GREEN}Stack deployment initiated!${NC}"
echo -e "${BLUE}Checking service status...${NC}"

# Wait a moment for services to start
sleep 5

# Show service status
docker stack services "$STACK_NAME"

echo -e "${GREEN}=== Deployment Complete ===${NC}"
echo -e "${BLUE}Access points:${NC}"
echo -e "  • Main App: https://unit-y-ai.io"
echo -e "  • API: https://api.unit-y-ai.io"
echo -e "  • N8N: https://n8n.unit-y-ai.io"
echo -e "  • Webhooks: https://webhooks.unit-y-ai.io"
echo -e "  • Traefik Dashboard: https://traefik.unit-y-ai.io"
echo -e "  • Grafana: https://grafana.unit-y-ai.io"

echo -e "${YELLOW}Note: Services may take a few minutes to become fully available${NC}"
echo -e "${YELLOW}Monitor with: docker stack services $STACK_NAME${NC}"
echo -e "${YELLOW}View logs with: docker service logs <service_name>${NC}"