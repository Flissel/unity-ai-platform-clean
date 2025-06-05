#!/usr/bin/env bash
set -euo pipefail

echo "▶️  Generiere .env-Dateien …"

# Hilfsfunktion
create() {
  local file="$1"
  shift
  if [[ -f $file ]]; then
    echo "  – überspringe $file (existiert bereits)"
  else
    printf "%s\n" "$@" > "$file"
    echo "  ✔ $file erstellt"
  fi
}

# 1) Binary Data
create .env.binarydata \
"N8N_DEFAULT_BINARY_DATA_MODE=filesystem
N8N_BINARY_DATA_STORAGE_PATH=/opt/unity/n8n/binaryData
N8N_AVAILABLE_BINARY_DATA_MODES=filesystem"

# 2) Database
create .env.database \
"DB_TYPE=postgresdb
DB_POSTGRESDB_HOST=postgres
DB_POSTGRESDB_PORT=5432
DB_POSTGRESDB_DATABASE=n8n
DB_POSTGRESDB_USER=n8n_user
DB_POSTGRESDB_PASSWORD=super-secret
DB_PING_INTERVAL_SECONDS=2"

# 3) Deployment
create .env.deployment \
"N8N_HOST=n8n.unit-y-ai.io
N8N_PORT=5678
N8N_PROTOCOL=https
WEBHOOK_URL=https://n8n.unit-y-ai.io/
N8N_EDITOR_BASE_URL=https://n8n.unit-y-ai.io
N8N_DISABLE_PRODUCTION_MAIN_MENU_METRICS=true"

# 4) Executions
create .env.executions \
"EXECUTIONS_MODE=regular
EXECUTIONS_DATA_SAVE_ON_SUCCESS=all
EXECUTIONS_DATA_SAVE_ON_ERROR=all
EXECUTIONS_TIMEOUT=0
EXECUTIONS_PROCESS_TIMEOUT=120"

# 5) Endpoints
create .env.endpoints \
"N8N_ENDPOINT_REST=rest
N8N_ENDPOINT_WEBHOOK=webhook
N8N_ENDPOINT_WEBHOOK_TEST=webhook-test
N8N_PAYLOAD_SIZE_MAX=16
N8N_FORMDATA_FILE_SIZE_MAX=200
N8N_METRICS=true
N8N_METRICS_PREFIX=n8n_"

# 6) Nodes
create .env.nodes \
"NODE_FUNCTION_ALLOW_EXTERNAL=pdf-lib,puppeteer
NODE_FUNCTION_ALLOW_BUILTIN=fs,path,crypto
N8N_LOAD_COMMUNITY_NODES=true"

# 7) Queue (Redis)
create .env.queue \
"EXECUTIONS_MODE=queue
QUEUE_BULL_REDIS_HOST=redis
QUEUE_BULL_REDIS_PORT=6379
QUEUE_BULL_REDIS_DB=0
QUEUE_BULL_REDIS_PREFIX=n8n_"

# 8) Security
create .env.security \
"N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=very-strong
N8N_COOKIE_SAME_SITE=lax"

# 9) Source Control (optional - leer anlegen)
create .env.sourcecontrol \
"# Beispiel für Enterprise-Git-Integration
# N8N_SOURCE_CONTROL_GIT_URL=
# N8N_SOURCE_CONTROL_GIT_BRANCH=main"

# 10) Task Runners
create .env.taskrunners \
"QUEUE_BULL_REDIS_HOST=redis
QUEUE_BULL_REDIS_PORT=6379
EXECUTIONS_PROCESS_TIMEOUT=0"

# 11) Timezone
create .env.timezone \
"N8N_TIMEZONE=Europe/Berlin"

# 12) User Management
create .env.usermanagement \
"N8N_USER_MANAGEMENT_DISABLED=false
N8N_2FA_REQUIRED=false"

# 13) Workflows
create .env.workflows \
"WORKFLOWS_DEFAULT_NAME=New workflow
WORKFLOWS_HISTORY_MAX=20
WORKFLOWS_TIMEOUT=300"

# 14) Common Defaults
create .env.common \
"N8N_ENCRYPTION_KEY=$(openssl rand -hex 32)
N8N_LOG_LEVEL=info"

echo "✅  Alle .env-Dateien generiert."
