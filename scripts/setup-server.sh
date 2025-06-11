#!/bin/bash

# Unity AI Server Setup Script
# This script automates the initial server setup for Unity AI deployment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   log_error "This script should not be run as root for security reasons"
   exit 1
fi

log "Starting Unity AI Server Setup..."

# Step 1: System Updates
log "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Step 2: Install Required Packages
log "Installing required packages..."
sudo apt install -y \
    curl \
    wget \
    git \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    openssl

# Step 3: Install Docker
log "Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    log_success "Docker installed successfully"
else
    log_warning "Docker already installed"
fi

# Step 4: Install Docker Compose
log "Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    log_success "Docker Compose installed successfully"
else
    log_warning "Docker Compose already installed"
fi

# Step 5: Create Application Directory
log "Creating application directory..."
APP_DIR="/opt/unityai"
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR
log_success "Application directory created: $APP_DIR"

# Step 6: Clone Repository (if not already present)
if [ ! -d "$APP_DIR/.git" ]; then
    log "Cloning Unity AI repository..."
    read -p "Enter your Git repository URL: " REPO_URL
    git clone $REPO_URL $APP_DIR
    cd $APP_DIR
else
    log_warning "Repository already exists, updating..."
    cd $APP_DIR
    git pull origin main
fi

# Step 7: Make Scripts Executable
log "Making scripts executable..."
chmod +x scripts/*.sh
chmod +x generate_envs.sh

# Step 8: Generate Environment Files
log "Generating environment files..."
if [ -f "generate_envs.sh" ]; then
    ./generate_envs.sh
    log_success "Environment files generated"
else
    log_warning "generate_envs.sh not found, skipping..."
fi

# Step 9: Initialize Docker Swarm (for secrets)
log "Initializing Docker Swarm..."
if ! docker info | grep -q "Swarm: active"; then
    docker swarm init
    log_success "Docker Swarm initialized"
else
    log_warning "Docker Swarm already active"
fi

# Step 10: Create Required Directories
log "Creating required directories..."
mkdir -p logs
mkdir -p traefik
mkdir -p backups
touch traefik/acme.json
chmod 600 traefik/acme.json

# Step 11: Setup Firewall (UFW)
log "Configuring firewall..."
if command -v ufw &> /dev/null; then
    sudo ufw --force enable
    sudo ufw allow ssh
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw reload
    log_success "Firewall configured"
else
    log_warning "UFW not available, skipping firewall setup"
fi

# Step 12: Setup Log Rotation
log "Setting up log rotation..."
sudo tee /etc/logrotate.d/unityai > /dev/null << EOF
$APP_DIR/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 $USER $USER
    postrotate
        cd $APP_DIR && docker-compose restart fastapi n8n
    endscript
}
EOF
log_success "Log rotation configured"

# Step 13: Create Backup Script
log "Creating backup script..."
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/unityai/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
docker-compose exec -T postgres pg_dump -U n8n_user n8n > $BACKUP_DIR/db_backup_$DATE.sql

# Backup n8n data
docker-compose exec -T n8n tar -czf - /opt/unity/n8n > $BACKUP_DIR/n8n_data_$DATE.tar.gz

# Keep only last 7 days
find $BACKUP_DIR -name "*backup*" -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

chmod +x backup.sh
log_success "Backup script created"

# Step 14: Setup Cron Job for Backups
log "Setting up automated backups..."
(crontab -l 2>/dev/null; echo "0 2 * * * cd $APP_DIR && ./backup.sh >> logs/backup.log 2>&1") | crontab -
log_success "Automated backups configured (daily at 2 AM)"

# Step 15: Create System Service (Optional)
log "Creating systemd service..."
sudo tee /etc/systemd/system/unityai.service > /dev/null << EOF
[Unit]
Description=Unity AI Docker Compose Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$APP_DIR
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0
User=$USER
Group=$USER

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable unityai.service
log_success "Systemd service created and enabled"

# Step 16: Display Next Steps
log_success "Unity AI Server Setup Complete!"

echo -e "\n${GREEN}=== NEXT STEPS ===${NC}"
echo -e "${YELLOW}1.${NC} Configure your environment variables:"
echo -e "   ${BLUE}nano .env.fastapi${NC}"
echo -e "   ${BLUE}nano .env.database${NC}"
echo -e "   ${BLUE}nano .env.security${NC}"
echo ""
echo -e "${YELLOW}2.${NC} Create Docker secrets:"
echo -e "   ${BLUE}echo 'your_db_password' | docker secret create pg_pw -${NC}"
echo -e "   ${BLUE}echo 'your_n8n_password' | docker secret create n8n_pw -${NC}"
echo ""
echo -e "${YELLOW}3.${NC} Update domain configuration in docker-compose.yml"
echo ""
echo -e "${YELLOW}4.${NC} Start the services:"
echo -e "   ${BLUE}docker-compose up -d${NC}"
echo ""
echo -e "${YELLOW}5.${NC} Import n8n workflows:"
echo -e "   ${BLUE}./scripts/import-workflows.sh${NC}"
echo ""
echo -e "${YELLOW}6.${NC} Generate n8n API key and update .env.fastapi"
echo ""
echo -e "${GREEN}For detailed instructions, see: DEPLOYMENT-GUIDE.md${NC}"
echo ""
echo -e "${RED}IMPORTANT:${NC} You may need to log out and back in for Docker group changes to take effect."

# Check if reboot is needed
if [ -f /var/run/reboot-required ]; then
    log_warning "System reboot is recommended to complete the setup"
fi

log_success "Setup script completed successfully!"
echo -e "${BLUE}Current directory: $(pwd)${NC}"
echo -e "${BLUE}Docker version: $(docker --version)${NC}"
echo -e "${BLUE}Docker Compose version: $(docker-compose --version)${NC}"