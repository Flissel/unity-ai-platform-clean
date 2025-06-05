#!/usr/bin/env python3
import os
from pathlib import Path
import secrets

ROOT = Path(__file__).resolve().parent

def create(filename: str, content: str) -> None:
    """Erzeugt eine Datei nur, wenn sie noch nicht existiert."""
    target = ROOT / filename
    if target.exists():
        print(f"  – überspringe {filename} (existiert bereits)")
    else:
        target.write_text(content.strip() + "\n", encoding="utf-8")
        print(f"  ✔ {filename} erstellt")

print("▶️  Generiere .env-Dateien …")

create(".env.binarydata", """
N8N_DEFAULT_BINARY_DATA_MODE=filesystem
N8N_BINARY_DATA_STORAGE_PATH=/opt/unity/n8n/binaryData
N8N_AVAILABLE_BINARY_DATA_MODES=filesystem
""")

create(".env.database", """
DB_TYPE=postgresdb
DB_POSTGRESDB_HOST=postgres
DB_POSTGRESDB_PORT=5432
DB_POSTGRESDB_DATABASE=n8n
DB_POSTGRESDB_USER=n8n_user
DB_POSTGRESDB_PASSWORD=super-secret
DB_PING_INTERVAL_SECONDS=2
""")

create(".env.deployment", """
N8N_HOST=n8n.unit-y-ai.io
N8N_PORT=5678
N8N_PROTOCOL=https
WEBHOOK_URL=https://n8n.unit-y-ai.io/
N8N_EDITOR_BASE_URL=https://n8n.unit-y-ai.io
N8N_DISABLE_PRODUCTION_MAIN_MENU_METRICS=true
""")

create(".env.executions", """
EXECUTIONS_MODE=regular
EXECUTIONS_DATA_SAVE_ON_SUCCESS=all
EXECUTIONS_DATA_SAVE_ON_ERROR=all
EXECUTIONS_TIMEOUT=0
EXECUTIONS_PROCESS_TIMEOUT=120
""")

create(".env.endpoints", """
N8N_ENDPOINT_REST=rest
N8N_ENDPOINT_WEBHOOK=webhook
N8N_ENDPOINT_WEBHOOK_TEST=webhook-test
N8N_PAYLOAD_SIZE_MAX=16
N8N_FORMDATA_FILE_SIZE_MAX=200
N8N_METRICS=true
N8N_METRICS_PREFIX=n8n_
""")

create(".env.nodes", """
NODE_FUNCTION_ALLOW_EXTERNAL=pdf-lib,puppeteer
NODE_FUNCTION_ALLOW_BUILTIN=fs,path,crypto
N8N_LOAD_COMMUNITY_NODES=true
""")

create(".env.queue", """
EXECUTIONS_MODE=queue
QUEUE_BULL_REDIS_HOST=redis
QUEUE_BULL_REDIS_PORT=6379
QUEUE_BULL_REDIS_DB=0
QUEUE_BULL_REDIS_PREFIX=n8n_
""")

create(".env.security", """
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=very-strong
N8N_COOKIE_SAME_SITE=lax
""")

create(".env.sourcecontrol", """
# N8N_SOURCE_CONTROL_GIT_URL=
# N8N_SOURCE_CONTROL_GIT_BRANCH=main
""")

create(".env.taskrunners", """
QUEUE_BULL_REDIS_HOST=redis
QUEUE_BULL_REDIS_PORT=6379
EXECUTIONS_PROCESS_TIMEOUT=0
""")

create(".env.timezone", """
N8N_TIMEZONE=Europe/Berlin
""")

create(".env.usermanagement", """
N8N_USER_MANAGEMENT_DISABLED=false
N8N_2FA_REQUIRED=false
""")

create(".env.workflows", """
WORKFLOWS_DEFAULT_NAME=New workflow
WORKFLOWS_HISTORY_MAX=20
WORKFLOWS_TIMEOUT=300
""")

create(".env.common", f"""
N8N_ENCRYPTION_KEY={secrets.token_hex(32)}
N8N_LOG_LEVEL=info
""")

print("✅  Alle .env-Dateien generiert.")
