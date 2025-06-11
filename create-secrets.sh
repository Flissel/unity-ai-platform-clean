#!/bin/bash

# UnityAI Docker Swarm Secrets Creation Script
# This script helps create the required secret files for Docker Swarm deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SECRETS_DIR="./secrets"

echo -e "${BLUE}=== UnityAI Docker Swarm Secrets Setup ===${NC}"

# Create secrets directory
mkdir -p "$SECRETS_DIR"
echo -e "${GREEN}Created secrets directory: $SECRETS_DIR${NC}"

# Function to generate random password
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
}

# Function to create secret file
create_secret_file() {
    local secret_name=$1
    local secret_file="$SECRETS_DIR/${secret_name}.txt"
    local prompt_message=$2
    local generate_random=${3:-false}
    
    if [ -f "$secret_file" ]; then
        echo -e "${YELLOW}Secret file $secret_file already exists${NC}"
        read -p "Do you want to overwrite it? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            return
        fi
    fi
    
    if [ "$generate_random" = true ]; then
        echo -e "${BLUE}$prompt_message${NC}"
        read -p "Generate random password? (Y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Nn]$ ]]; then
            read -s -p "Enter value: " secret_value
            echo
        else
            secret_value=$(generate_password)
            echo -e "${GREEN}Generated random password${NC}"
        fi
    else
        echo -e "${BLUE}$prompt_message${NC}"
        read -s -p "Enter value: " secret_value
        echo
    fi
    
    echo "$secret_value" > "$secret_file"
    chmod 600 "$secret_file"
    echo -e "${GREEN}Created: $secret_file${NC}"
}

echo -e "${YELLOW}This script will help you create all required secret files for Docker Swarm deployment.${NC}"
echo -e "${YELLOW}You can generate random passwords for database/service passwords or enter your own values.${NC}"
echo

# Database secrets
echo -e "${BLUE}=== Database Secrets ===${NC}"
create_secret_file "postgres_password" "PostgreSQL database password" true
create_secret_file "redis_pw" "Redis password" true

# N8N secrets
echo -e "${BLUE}=== N8N Secrets ===${NC}"
create_secret_file "n8n_admin_password" "N8N admin password" true
create_secret_file "n8n_encryption_key" "N8N encryption key (32+ characters)" true
create_secret_file "n8n_api_key" "N8N API key (get from N8N interface after setup)"

# Cloudflare secrets
echo -e "${BLUE}=== Cloudflare Secrets ===${NC}"
create_secret_file "cloudflare_email" "Cloudflare account email"
create_secret_file "cloudflare_token" "Cloudflare API token (with DNS edit permissions)"

# API Keys
echo -e "${BLUE}=== External API Keys ===${NC}"
create_secret_file "openai_api_key" "OpenAI API key"
create_secret_file "anthropic_api_key" "Anthropic API key (optional)"
create_secret_file "groq_api_key" "Groq API key (optional)"

# Monitoring secrets
echo -e "${BLUE}=== Monitoring Secrets ===${NC}"
create_secret_file "grafana_admin_password" "Grafana admin password" true

# Runner token (if using GitHub Actions runner)
echo -e "${BLUE}=== GitHub Actions Runner (Optional) ===${NC}"
read -p "Do you want to set up GitHub Actions runner? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    create_secret_file "runner_token" "GitHub Actions runner token"
else
    echo "PLACEHOLDER" > "$SECRETS_DIR/runner_token.txt"
    chmod 600 "$SECRETS_DIR/runner_token.txt"
    echo -e "${YELLOW}Created placeholder runner_token.txt${NC}"
fi

echo
echo -e "${GREEN}=== Secrets Creation Complete ===${NC}"
echo -e "${BLUE}Created secret files in: $SECRETS_DIR${NC}"
echo
echo -e "${YELLOW}Important Security Notes:${NC}"
echo -e "  • Secret files are set to 600 permissions (owner read/write only)"
echo -e "  • Do NOT commit the secrets directory to version control"
echo -e "  • Backup your secrets securely"
echo -e "  • The secrets directory should be added to .gitignore"
echo
echo -e "${BLUE}Next steps:${NC}"
echo -e "  1. Review and update any placeholder values in the secret files"
echo -e "  2. Run: ./deploy-swarm.sh to deploy the stack"
echo -e "  3. Access N8N to get the API key and update n8n_api_key.txt if needed"

# Add secrets directory to .gitignore if it exists
if [ -f ".gitignore" ]; then
    if ! grep -q "^secrets/" .gitignore; then
        echo "secrets/" >> .gitignore
        echo -e "${GREEN}Added secrets/ to .gitignore${NC}"
    fi
else
    echo "secrets/" > .gitignore
    echo -e "${GREEN}Created .gitignore with secrets/ entry${NC}"
fi