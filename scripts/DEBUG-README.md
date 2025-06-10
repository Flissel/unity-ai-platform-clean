# UnityAI Debug Scripts

This directory contains debug scripts to help troubleshoot and fix issues with the UnityAI Docker Swarm deployment.

## Scripts Overview

### 1. `debug-server.sh` (Linux/macOS)
Comprehensive debug script that connects to the server and performs extensive diagnostics.

**Features:**
- Tests SSH connectivity
- Checks Docker system status
- Analyzes Docker Swarm configuration
- Examines UnityAI stack services
- Collects service logs
- Tests application endpoints
- Generates comprehensive reports
- Downloads log archives

**Usage:**
```bash
# Basic usage
./debug-server.sh

# With custom command
./debug-server.sh "docker stack ps unityai"

# With custom server
SERVER_HOST=myserver.com ./debug-server.sh

# Show help
./debug-server.sh --help
```

### 2. `debug-server.ps1` (Windows PowerShell)
PowerShell version of the debug script for Windows users.

**Usage:**
```powershell
# Basic usage
.\debug-server.ps1

# With parameters
.\debug-server.ps1 -CustomCommand "docker stack ps unityai" -ServerHost "myserver.com"

# Show help
.\debug-server.ps1 -Help
```

### 3. `quick-debug.sh` (Interactive Menu)
Interactive script with menu-driven options for common debug and fix operations.

**Features:**
- Interactive menu interface
- Quick status checks
- Service log viewing
- Image building and deployment
- HTTP 521 error fixing
- Endpoint testing

**Usage:**
```bash
# Interactive mode
./quick-debug.sh

# Direct commands
./quick-debug.sh status
./quick-debug.sh build
./quick-debug.sh fix521
./quick-debug.sh endpoints
```

## Environment Variables

All scripts support these environment variables:

- `SERVER_HOST`: Target server hostname (default: `unit-y-ai.io`)
- `SSH_USER`: SSH username (default: `root`)
- `SSH_KEY`: SSH private key path (default: `~/.ssh/id_rsa`)

## Prerequisites

### For Linux/macOS:
- SSH client
- Docker (for building images)
- curl (for endpoint testing)
- jq (optional, for JSON parsing)

### For Windows:
- OpenSSH client or WSL
- Docker Desktop
- PowerShell 5.1 or later

## Common Use Cases

### 1. HTTP 521 Error (Cloudflare)
This error typically indicates that the origin server is not responding.

**Quick Fix:**
```bash
./quick-debug.sh fix521
```

**Manual Steps:**
1. Check service status: `./quick-debug.sh status`
2. Build missing images: `./quick-debug.sh build`
3. Restart services: `./quick-debug.sh restart`
4. Test endpoints: `./quick-debug.sh endpoints`

### 2. Services Not Starting
**Diagnosis:**
```bash
./debug-server.sh
```

**Common Causes:**
- Missing Docker images
- Insufficient resources
- Configuration errors
- Network issues

### 3. Performance Issues
**Check Resources:**
```bash
./debug-server.sh "docker stats --no-stream"
./debug-server.sh "df -h && free -h"
```

### 4. Service Logs Analysis
**View Specific Service:**
```bash
./quick-debug.sh logs
```

**Or directly:**
```bash
./debug-server.sh "docker service logs --tail 100 unityai_app"
```

## Troubleshooting the Debug Scripts

### SSH Connection Issues
1. Verify SSH key permissions: `chmod 600 ~/.ssh/id_rsa`
2. Test manual connection: `ssh -i ~/.ssh/id_rsa root@unit-y-ai.io`
3. Check firewall settings
4. Verify server is accessible

### Permission Issues
1. Ensure SSH key has proper permissions
2. Verify user has Docker permissions on server
3. Check sudo requirements

### Script Execution Issues
**Linux/macOS:**
```bash
chmod +x debug-server.sh quick-debug.sh
```

**Windows:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Output Files

The debug scripts generate several output files:

- `debug-results-YYYYMMDD-HHMMSS.log`: Complete debug session log
- `unityai-logs-YYYYMMDD-HHMMSS.tar.gz`: Downloaded service logs archive
- `*.tar.gz`: Docker image archives (temporary)

## Advanced Usage

### Custom Debug Commands
```bash
# Check specific service
./debug-server.sh "docker service inspect unityai_app"

# Monitor real-time logs
./debug-server.sh "docker service logs -f unityai_app"

# Check container processes
./debug-server.sh "docker service ps unityai_app --no-trunc"
```

### Batch Operations
```bash
# Run multiple checks
for cmd in "docker stack services unityai" "docker node ls" "docker network ls"; do
    ./debug-server.sh "$cmd"
done
```

### Remote Image Building
If you need to build images directly on the server:

```bash
./debug-server.sh "cd /opt/unityai && docker build -t unityai-app ."
./debug-server.sh "cd /opt/unityai && docker build -t unityai-frontend ./frontend/"
```

## Security Considerations

1. **SSH Keys**: Use key-based authentication instead of passwords
2. **Permissions**: Ensure SSH keys have restrictive permissions (600)
3. **Logs**: Debug logs may contain sensitive information - handle appropriately
4. **Network**: Use VPN or secure networks when possible

## Integration with CI/CD

These scripts can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions step
- name: Debug deployment
  run: |
    ./scripts/debug-server.sh "docker stack services unityai"
  env:
    SERVER_HOST: ${{ secrets.SERVER_HOST }}
    SSH_KEY: ${{ secrets.SSH_PRIVATE_KEY }}
```

## Support

If you encounter issues with these debug scripts:

1. Check the generated log files
2. Verify prerequisites are installed
3. Test SSH connectivity manually
4. Review server logs
5. Check Docker daemon status on server

For additional help, refer to the main project documentation or create an issue in the repository.