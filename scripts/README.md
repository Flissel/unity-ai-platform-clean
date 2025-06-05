# Unity AI Platform - Scripts Directory

This directory contains all automation and utility scripts for the Unity AI Platform.

## 🚀 Deployment Scripts

### Production Deployment
- **`setup-production.sh`** - Complete production environment setup
  - Collects configuration from user
  - Installs system dependencies
  - Configures firewall and security
  - Sets up systemd service
  - Creates backup procedures

- **`deploy-production.sh`** - Automated production deployment
  - Creates backups before deployment
  - Pulls/builds latest images
  - Performs health checks
  - Supports rollback on failure
  - Cleans up old backups

### Server Setup
- **`setup-server.sh`** - Linux server preparation script
- **`setup-server.ps1`** - Windows server preparation script

## 🔧 Development Scripts

### Environment Management
- **`generate_envs.py`** - Python script to generate environment files
- **`generate_envs.sh`** - Shell script for environment setup

### Testing & Development
- **`worker_example.py`** - Example worker implementation

## 📋 Script Usage

### Quick Production Setup
```bash
# Make scripts executable
chmod +x scripts/*.sh

# Run production setup (interactive)
./scripts/setup-production.sh

# Deploy services
./scripts/deploy-production.sh deploy
```

### Development Environment
```bash
# Generate development environment
./scripts/generate_envs.sh development

# Or use Python script
python scripts/generate_envs.py --env development
```

### Server Preparation
```bash
# Linux server setup
./scripts/setup-server.sh

# Windows server setup (PowerShell)
.\scripts\setup-server.ps1
```

## 🛡️ Security Considerations

- All scripts validate input parameters
- Sensitive data is handled securely
- Backup procedures are included
- Rollback capabilities are provided
- Scripts follow security best practices

## 📊 Script Features

### Error Handling
- Comprehensive error checking
- Graceful failure handling
- Detailed logging
- User-friendly error messages

### Automation
- Minimal user interaction required
- Intelligent defaults
- Progress indicators
- Confirmation prompts for destructive operations

### Monitoring
- Health checks after deployment
- Service status verification
- Performance monitoring setup
- Log aggregation configuration

## 🔄 Maintenance Scripts

### Backup Operations
```bash
# Manual backup
./scripts/deploy-production.sh backup

# Restore from backup
./scripts/deploy-production.sh rollback TIMESTAMP
```

### Health Checks
```bash
# Check all services
./scripts/deploy-production.sh health-check

# Detailed system status
./scripts/deploy-production.sh status
```

### Updates
```bash
# Update all services
./scripts/deploy-production.sh update

# Update specific service
./scripts/deploy-production.sh update SERVICE_NAME
```

## 📝 Script Development Guidelines

### Standards
- Use bash for Linux scripts
- Use PowerShell for Windows scripts
- Include comprehensive error handling
- Add progress indicators for long operations
- Document all parameters and options

### Testing
- Test scripts in isolated environments
- Verify rollback procedures
- Test with various input scenarios
- Validate error handling paths

### Documentation
- Include usage examples
- Document all parameters
- Explain script dependencies
- Provide troubleshooting information

## 🆘 Troubleshooting

### Common Issues

1. **Permission Denied**
   ```bash
   chmod +x scripts/*.sh
   ```

2. **Missing Dependencies**
   ```bash
   # Install required tools
   sudo apt update && sudo apt install -y curl wget git
   ```

3. **Network Issues**
   - Check firewall settings
   - Verify DNS resolution
   - Test connectivity to external services

4. **Service Startup Failures**
   - Check service logs
   - Verify configuration files
   - Ensure all dependencies are running

### Getting Help

- Check script output for error messages
- Review log files in `/var/log/unityai/`
- Use `--help` flag with scripts for usage information
- Refer to main documentation in `/docs` directory

---

**Note**: Always test scripts in a development environment before running in production.