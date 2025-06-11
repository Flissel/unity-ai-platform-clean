#!/bin/bash
# Export Development Environment Configuration
# This script exports n8n workflows and configurations for GitOps

set -e

echo "🔄 Exporting Unity AI Platform Development Configuration..."

# Configuration
EXPORT_DIR="./exports/$(date +%Y%m%d_%H%M%S)"
N8N_API_URL="${N8N_API_URL:-http://localhost:5678/api/v1}"
N8N_API_KEY="${N8N_API_KEY}"

# Create export directory
mkdir -p "$EXPORT_DIR"

echo "📁 Export directory: $EXPORT_DIR"

# Check if n8n API is available
if ! curl -s "$N8N_API_URL/workflows" -H "X-N8N-API-KEY: $N8N_API_KEY" > /dev/null; then
    echo "❌ Error: n8n API not accessible at $N8N_API_URL"
    echo "   Make sure n8n is running and N8N_API_KEY is set"
    exit 1
fi

# Export workflows
echo "📋 Exporting workflows..."
curl -s "$N8N_API_URL/workflows" \
    -H "X-N8N-API-KEY: $N8N_API_KEY" \
    | jq '.' > "$EXPORT_DIR/workflows.json"

# Export credentials (metadata only, no sensitive data)
echo "🔑 Exporting credential metadata..."
curl -s "$N8N_API_URL/credentials" \
    -H "X-N8N-API-KEY: $N8N_API_KEY" \
    | jq '[.[] | {id, name, type, nodesAccess}]' > "$EXPORT_DIR/credentials_metadata.json"

# Export executions (last 50)
echo "⚡ Exporting recent executions..."
curl -s "$N8N_API_URL/executions?limit=50" \
    -H "X-N8N-API-KEY: $N8N_API_KEY" \
    | jq '.' > "$EXPORT_DIR/executions.json"

# Export environment configuration (without secrets)
echo "⚙️ Exporting environment configuration..."
cp -r ./n8n/env "$EXPORT_DIR/"

# Remove sensitive data from exported env files
find "$EXPORT_DIR/env" -name "*.env*" -type f -exec sed -i 's/=.*/=PLACEHOLDER/' {} \;

# Create export manifest
echo "📄 Creating export manifest..."
cat > "$EXPORT_DIR/manifest.json" << EOF
{
  "export_date": "$(date -Iseconds)",
  "export_type": "development",
  "platform_version": "1.0.0",
  "n8n_api_url": "$N8N_API_URL",
  "files": {
    "workflows": "workflows.json",
    "credentials_metadata": "credentials_metadata.json",
    "executions": "executions.json",
    "environment": "env/"
  },
  "notes": "Exported from development environment. Sensitive data has been removed."
}
EOF

# Create README for the export
cat > "$EXPORT_DIR/README.md" << EOF
# Unity AI Platform Export

**Export Date:** $(date)
**Environment:** Development
**Export Directory:** $EXPORT_DIR

## Contents

- \`workflows.json\` - All n8n workflows
- \`credentials_metadata.json\` - Credential metadata (no sensitive data)
- \`executions.json\` - Recent execution history
- \`env/\` - Environment configuration files (sanitized)
- \`manifest.json\` - Export metadata

## Import Instructions

To import this configuration to another environment:

\`\`\`bash
./scripts/import-prod.sh $EXPORT_DIR
\`\`\`

## Security Notes

- All sensitive data (API keys, passwords) has been replaced with placeholders
- Credential data contains only metadata, not actual secrets
- Review and update all configuration before importing to production
EOF

echo "✅ Export completed successfully!"
echo "📁 Export location: $EXPORT_DIR"
echo "📖 See $EXPORT_DIR/README.md for import instructions"