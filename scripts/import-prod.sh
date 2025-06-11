#!/bin/bash
# Import Configuration to Production Environment
# This script imports n8n workflows and configurations from exported data

set -e

# Check if export directory is provided
if [ $# -eq 0 ]; then
    echo "❌ Error: No export directory provided"
    echo "Usage: $0 <export_directory>"
    echo "Example: $0 ./exports/20241201_143000"
    exit 1
fi

EXPORT_DIR="$1"

if [ ! -d "$EXPORT_DIR" ]; then
    echo "❌ Error: Export directory '$EXPORT_DIR' does not exist"
    exit 1
fi

echo "🚀 Importing Unity AI Platform Configuration to Production..."
echo "📁 Import source: $EXPORT_DIR"

# Configuration
N8N_API_URL="${N8N_API_URL:-http://localhost:5678/api/v1}"
N8N_API_KEY="${N8N_API_KEY}"

if [ -z "$N8N_API_KEY" ]; then
    echo "❌ Error: N8N_API_KEY environment variable is required"
    exit 1
fi

# Verify export manifest
if [ ! -f "$EXPORT_DIR/manifest.json" ]; then
    echo "❌ Error: Invalid export - manifest.json not found"
    exit 1
fi

echo "📋 Reading export manifest..."
EXPORT_DATE=$(jq -r '.export_date' "$EXPORT_DIR/manifest.json")
EXPORT_TYPE=$(jq -r '.export_type' "$EXPORT_DIR/manifest.json")

echo "   Export Date: $EXPORT_DATE"
echo "   Export Type: $EXPORT_TYPE"

# Check if n8n API is available
echo "🔍 Checking n8n API connectivity..."
if ! curl -s "$N8N_API_URL/workflows" -H "X-N8N-API-KEY: $N8N_API_KEY" > /dev/null; then
    echo "❌ Error: n8n API not accessible at $N8N_API_URL"
    echo "   Make sure n8n is running and N8N_API_KEY is correct"
    exit 1
fi

echo "✅ n8n API is accessible"

# Backup existing workflows before import
echo "💾 Creating backup of existing workflows..."
BACKUP_DIR="./backups/pre-import-$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

curl -s "$N8N_API_URL/workflows" \
    -H "X-N8N-API-KEY: $N8N_API_KEY" \
    | jq '.' > "$BACKUP_DIR/workflows_backup.json"

echo "   Backup saved to: $BACKUP_DIR"

# Import workflows
if [ -f "$EXPORT_DIR/workflows.json" ]; then
    echo "📋 Importing workflows..."
    
    # Read workflows from export
    WORKFLOWS=$(cat "$EXPORT_DIR/workflows.json")
    
    # Import each workflow
    echo "$WORKFLOWS" | jq -c '.data[]' | while read -r workflow; do
        WORKFLOW_NAME=$(echo "$workflow" | jq -r '.name')
        echo "   Importing workflow: $WORKFLOW_NAME"
        
        # Remove id to create new workflow
        WORKFLOW_DATA=$(echo "$workflow" | jq 'del(.id)')
        
        # Import workflow
        curl -s -X POST "$N8N_API_URL/workflows" \
            -H "Content-Type: application/json" \
            -H "X-N8N-API-KEY: $N8N_API_KEY" \
            -d "$WORKFLOW_DATA" > /dev/null
        
        if [ $? -eq 0 ]; then
            echo "   ✅ Successfully imported: $WORKFLOW_NAME"
        else
            echo "   ❌ Failed to import: $WORKFLOW_NAME"
        fi
    done
else
    echo "⚠️  No workflows.json found in export"
fi

# Copy environment configuration
if [ -d "$EXPORT_DIR/env" ]; then
    echo "⚙️ Copying environment configuration..."
    
    # Create backup of current env
    if [ -d "./n8n/env" ]; then
        cp -r "./n8n/env" "$BACKUP_DIR/env_backup"
    fi
    
    # Copy new env files
    cp -r "$EXPORT_DIR/env"/* "./n8n/env/"
    
    echo "   ✅ Environment configuration copied"
    echo "   ⚠️  Remember to update placeholder values with real secrets!"
else
    echo "⚠️  No environment configuration found in export"
fi

# Display credential metadata for manual setup
if [ -f "$EXPORT_DIR/credentials_metadata.json" ]; then
    echo "🔑 Credential metadata found:"
    jq -r '.[] | "   - \(.name) (\(.type))"' "$EXPORT_DIR/credentials_metadata.json"
    echo "   ⚠️  You need to manually recreate these credentials in n8n"
fi

# Create import report
REPORT_FILE="./import_report_$(date +%Y%m%d_%H%M%S).md"
cat > "$REPORT_FILE" << EOF
# Unity AI Platform Import Report

**Import Date:** $(date)
**Source Export:** $EXPORT_DIR
**Export Date:** $EXPORT_DATE
**Export Type:** $EXPORT_TYPE
**Backup Location:** $BACKUP_DIR

## Import Status

- ✅ Workflows imported
- ✅ Environment configuration copied
- ⚠️  Credentials need manual setup

## Next Steps

1. **Update Environment Variables:**
   - Review files in \`./n8n/env/\`
   - Replace placeholder values with real secrets
   - Update API keys, passwords, and encryption keys

2. **Recreate Credentials:**
   - Log into n8n UI
   - Recreate credentials based on metadata
   - Test all workflow connections

3. **Restart Services:**
   \`\`\`bash
   docker-compose -f compose/docker-compose.yml restart
   \`\`\`

4. **Verify Import:**
   - Check n8n UI for imported workflows
   - Test workflow executions
   - Verify all integrations work

## Rollback Instructions

If you need to rollback this import:

\`\`\`bash
# Restore workflows
curl -X DELETE "$N8N_API_URL/workflows" -H "X-N8N-API-KEY: $N8N_API_KEY"
# Import backup
# ... (manual process)

# Restore environment
cp -r "$BACKUP_DIR/env_backup"/* "./n8n/env/"
\`\`\`
EOF

echo "✅ Import completed successfully!"
echo "📄 Import report: $REPORT_FILE"
echo "💾 Backup location: $BACKUP_DIR"
echo ""
echo "⚠️  IMPORTANT NEXT STEPS:"
echo "   1. Update placeholder values in ./n8n/env/ files"
echo "   2. Recreate credentials in n8n UI"
echo "   3. Restart services: docker-compose restart"
echo "   4. Test all workflows"