#!/bin/bash
# Unity AI Platform - Complete Server Setup Script
# Dieses Skript richtet einen kompletten Linux-Server für Unity AI ein
# Führt alle notwendigen Installationen, Konfigurationen und Deployments durch

set -euo pipefail

# =============================================================================
# KONFIGURATION
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="/var/log/unityai-complete-setup-$(date +%Y%m%d-%H%M%S).log"
LOCK_FILE="/tmp/unityai-setup.lock"

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# =============================================================================
# LOGGING UND HILFSFUNKTIONEN
# =============================================================================
log() {
    echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_info() {
    log "${BLUE}[INFO]${NC} $1"
}

log_success() {
    log "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    log "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    log "${RED}[ERROR]${NC} $1"
}

log_step() {
    log "${PURPLE}[STEP]${NC} $1"
}

log_substep() {
    log "${CYAN}  → ${NC}$1"
}

# Fehlerbehandlung
trap 'cleanup_on_error' ERR
trap 'cleanup_on_exit' EXIT

cleanup_on_error() {
    log_error "Setup fehlgeschlagen bei Zeile $LINENO. Exit Code: $?"
    cleanup_on_exit
    exit 1
}

cleanup_on_exit() {
    if [[ -f "$LOCK_FILE" ]]; then
        rm -f "$LOCK_FILE"
    fi
}

# Lock-File prüfen
check_lock() {
    if [[ -f "$LOCK_FILE" ]]; then
        log_error "Setup läuft bereits (Lock-File: $LOCK_FILE)"
        exit 1
    fi
    echo $$ > "$LOCK_FILE"
}

# Root-Rechte prüfen
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "Dieses Skript muss als root ausgeführt werden"
        log_info "Verwende: sudo $0"
        exit 1
    fi
}

# Betriebssystem erkennen
detect_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$ID
        VER=$VERSION_ID
    else
        log_error "Kann Betriebssystem nicht erkennen"
        exit 1
    fi
    log_info "Erkanntes OS: $OS $VER"
}

# =============================================================================
# SYSTEM-UPDATES UND GRUNDINSTALLATION
# =============================================================================
update_system() {
    log_step "System-Updates installieren..."
    
    case $OS in
        ubuntu|debian)
            log_substep "APT-Paketlisten aktualisieren"
            apt-get update -y
            
            log_substep "System-Upgrade durchführen"
            apt-get upgrade -y
            
            log_substep "Grundlegende Pakete installieren"
            apt-get install -y \
                curl \
                wget \
                git \
                unzip \
                software-properties-common \
                apt-transport-https \
                ca-certificates \
                gnupg \
                lsb-release \
                htop \
                nano \
                vim \
                ufw \
                fail2ban \
                openssl \
                jq \
                tree
            ;;
        centos|rhel|fedora)
            log_substep "YUM/DNF-Pakete aktualisieren"
            if command -v dnf &> /dev/null; then
                dnf update -y
                dnf install -y curl wget git unzip openssl jq tree htop nano vim firewalld fail2ban
            else
                yum update -y
                yum install -y curl wget git unzip openssl jq tree htop nano vim firewalld fail2ban
            fi
            ;;
        *)
            log_error "Nicht unterstütztes Betriebssystem: $OS"
            exit 1
            ;;
    esac
    
    log_success "System-Updates abgeschlossen"
}

# =============================================================================
# DOCKER INSTALLATION
# =============================================================================
install_docker() {
    log_step "Docker installieren..."
    
    if command -v docker &> /dev/null; then
        log_info "Docker ist bereits installiert"
        docker --version
        return 0
    fi
    
    case $OS in
        ubuntu|debian)
            log_substep "Docker GPG-Schlüssel hinzufügen"
            curl -fsSL https://download.docker.com/linux/$OS/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
            
            log_substep "Docker Repository hinzufügen"
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/$OS $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
            
            log_substep "Docker installieren"
            apt-get update -y
            apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
            ;;
        centos|rhel|fedora)
            log_substep "Docker Repository hinzufügen"
            if command -v dnf &> /dev/null; then
                dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
                dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
            else
                yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
                yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
            fi
            ;;
    esac
    
    log_substep "Docker-Service starten und aktivieren"
    systemctl start docker
    systemctl enable docker
    
    log_substep "Docker-Gruppe erstellen und Benutzer hinzufügen"
    groupadd -f docker
    
    log_success "Docker erfolgreich installiert"
    docker --version
}

# =============================================================================
# DOCKER COMPOSE INSTALLATION
# =============================================================================
install_docker_compose() {
    log_step "Docker Compose installieren..."
    
    if docker compose version &> /dev/null; then
        log_info "Docker Compose ist bereits installiert"
        docker compose version
        return 0
    fi
    
    log_substep "Neueste Docker Compose Version ermitteln"
    COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | jq -r .tag_name)
    
    log_substep "Docker Compose $COMPOSE_VERSION herunterladen"
    curl -L "https://github.com/docker/compose/releases/download/$COMPOSE_VERSION/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    
    log_substep "Ausführungsrechte setzen"
    chmod +x /usr/local/bin/docker-compose
    
    log_success "Docker Compose erfolgreich installiert"
    docker-compose --version
}

# =============================================================================
# FIREWALL KONFIGURATION
# =============================================================================
configure_firewall() {
    log_step "Firewall konfigurieren..."
    
    case $OS in
        ubuntu|debian)
            log_substep "UFW konfigurieren"
            ufw --force reset
            ufw default deny incoming
            ufw default allow outgoing
            
            # SSH
            ufw allow ssh
            ufw allow 22/tcp
            
            # HTTP/HTTPS
            ufw allow 80/tcp
            ufw allow 443/tcp
            
            # Docker Swarm
            ufw allow 2376/tcp
            ufw allow 2377/tcp
            ufw allow 7946/tcp
            ufw allow 7946/udp
            ufw allow 4789/udp
            
            ufw --force enable
            ;;
        centos|rhel|fedora)
            log_substep "Firewalld konfigurieren"
            systemctl start firewalld
            systemctl enable firewalld
            
            # Standard-Services
            firewall-cmd --permanent --add-service=ssh
            firewall-cmd --permanent --add-service=http
            firewall-cmd --permanent --add-service=https
            
            # Docker Swarm Ports
            firewall-cmd --permanent --add-port=2376/tcp
            firewall-cmd --permanent --add-port=2377/tcp
            firewall-cmd --permanent --add-port=7946/tcp
            firewall-cmd --permanent --add-port=7946/udp
            firewall-cmd --permanent --add-port=4789/udp
            
            firewall-cmd --reload
            ;;
    esac
    
    log_success "Firewall erfolgreich konfiguriert"
}

# =============================================================================
# FAIL2BAN KONFIGURATION
# =============================================================================
configure_fail2ban() {
    log_step "Fail2Ban konfigurieren..."
    
    log_substep "Fail2Ban-Konfiguration erstellen"
    cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3
ignoreip = 127.0.0.1/8 ::1

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600

[docker-auth]
enabled = true
filter = docker-auth
logpath = /var/log/docker.log
maxretry = 3
bantime = 3600
EOF
    
    log_substep "Fail2Ban starten und aktivieren"
    systemctl start fail2ban
    systemctl enable fail2ban
    
    log_success "Fail2Ban erfolgreich konfiguriert"
}

# =============================================================================
# BENUTZER UND VERZEICHNISSE
# =============================================================================
setup_user_and_directories() {
    log_step "Benutzer und Verzeichnisse einrichten..."
    
    log_substep "Unity AI Benutzer erstellen"
    if ! id "unityai" &>/dev/null; then
        useradd -m -s /bin/bash unityai
        usermod -aG docker unityai
        log_info "Benutzer 'unityai' erstellt"
    else
        log_info "Benutzer 'unityai' existiert bereits"
    fi
    
    log_substep "Projektverzeichnisse erstellen"
    directories=(
        "/opt/unityai"
        "/opt/unityai/data"
        "/opt/unityai/logs"
        "/opt/unityai/uploads"
        "/opt/unityai/scripts"
        "/opt/unityai/config"
        "/opt/unityai/backups"
        "/var/log/unityai"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
        chown -R unityai:unityai "$dir"
        log_substep "Verzeichnis erstellt: $dir"
    done
    
    log_success "Benutzer und Verzeichnisse erfolgreich eingerichtet"
}

# =============================================================================
# PROJEKT DEPLOYMENT
# =============================================================================
deploy_project() {
    log_step "Unity AI Projekt deployen..."
    
    log_substep "Projekt-Code kopieren"
    cp -r "$PROJECT_ROOT"/* /opt/unityai/
    chown -R unityai:unityai /opt/unityai/
    
    log_substep "Skripte ausführbar machen"
    chmod +x /opt/unityai/scripts/*.sh
    
    log_success "Projekt erfolgreich deployed"
}

# =============================================================================
# DOCKER SWARM SETUP
# =============================================================================
setup_docker_swarm() {
    log_step "Docker Swarm einrichten..."
    
    cd /opt/unityai
    
    log_substep "Docker Swarm Setup-Skript ausführen"
    sudo -u unityai bash scripts/setup-docker-secrets.sh
    
    log_substep "Docker Swarm Deployment"
    sudo -u unityai bash scripts/deploy-swarm.sh
    
    log_success "Docker Swarm erfolgreich eingerichtet"
}

# =============================================================================
# MONITORING UND LOGGING
# =============================================================================
setup_monitoring() {
    log_step "Monitoring und Logging einrichten..."
    
    log_substep "Logrotate für Unity AI konfigurieren"
    cat > /etc/logrotate.d/unityai << 'EOF'
/var/log/unityai/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 unityai unityai
    postrotate
        systemctl reload rsyslog > /dev/null 2>&1 || true
    endscript
}
EOF
    
    log_substep "Systemd-Service für Unity AI erstellen"
    cat > /etc/systemd/system/unityai.service << 'EOF'
[Unit]
Description=Unity AI Platform
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/unityai
User=unityai
Group=unityai
ExecStart=/bin/bash scripts/deploy-swarm.sh
ExecStop=/usr/bin/docker stack rm unityai
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable unityai.service
    
    log_success "Monitoring und Logging erfolgreich eingerichtet"
}

# =============================================================================
# BACKUP-SYSTEM
# =============================================================================
setup_backup() {
    log_step "Backup-System einrichten..."
    
    log_substep "Backup-Skript erstellen"
    cat > /opt/unityai/scripts/backup.sh << 'EOF'
#!/bin/bash
# Unity AI Backup Script

BACKUP_DIR="/opt/unityai/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/unityai_backup_$DATE.tar.gz"

# Docker Volumes sichern
docker run --rm -v unityai_postgres_data:/data -v $BACKUP_DIR:/backup alpine tar czf /backup/postgres_$DATE.tar.gz -C /data .
docker run --rm -v unityai_redis_data:/data -v $BACKUP_DIR:/backup alpine tar czf /backup/redis_$DATE.tar.gz -C /data .
docker run --rm -v unityai_n8n_data:/data -v $BACKUP_DIR:/backup alpine tar czf /backup/n8n_$DATE.tar.gz -C /data .

# Konfiguration sichern
tar czf $BACKUP_DIR/config_$DATE.tar.gz -C /opt/unityai config/

# Alte Backups löschen (älter als 30 Tage)
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup abgeschlossen: $DATE"
EOF
    
    chmod +x /opt/unityai/scripts/backup.sh
    chown unityai:unityai /opt/unityai/scripts/backup.sh
    
    log_substep "Cron-Job für tägliche Backups einrichten"
    echo "0 2 * * * /opt/unityai/scripts/backup.sh >> /var/log/unityai/backup.log 2>&1" | crontab -u unityai -
    
    log_success "Backup-System erfolgreich eingerichtet"
}

# =============================================================================
# SYSTEM-OPTIMIERUNG
# =============================================================================
optimize_system() {
    log_step "System optimieren..."
    
    log_substep "Kernel-Parameter für Docker optimieren"
    cat >> /etc/sysctl.conf << 'EOF'
# Unity AI Docker Optimierungen
vm.max_map_count=262144
net.core.somaxconn=65535
net.ipv4.tcp_max_syn_backlog=65535
net.ipv4.ip_forward=1
EOF
    
    sysctl -p
    
    log_substep "Docker-Daemon optimieren"
    mkdir -p /etc/docker
    cat > /etc/docker/daemon.json << 'EOF'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "live-restore": true,
  "userland-proxy": false,
  "experimental": false
}
EOF
    
    systemctl restart docker
    
    log_success "System erfolgreich optimiert"
}

# =============================================================================
# GESUNDHEITSCHECKS
# =============================================================================
run_health_checks() {
    log_step "Gesundheitschecks durchführen..."
    
    log_substep "Docker-Status prüfen"
    if systemctl is-active --quiet docker; then
        log_info "✓ Docker läuft"
    else
        log_error "✗ Docker läuft nicht"
    fi
    
    log_substep "Docker Swarm-Status prüfen"
    if docker info --format '{{.Swarm.LocalNodeState}}' | grep -q "active"; then
        log_info "✓ Docker Swarm ist aktiv"
    else
        log_warning "✗ Docker Swarm ist nicht aktiv"
    fi
    
    log_substep "Unity AI Services prüfen"
    if docker stack ls | grep -q "unityai"; then
        log_info "✓ Unity AI Stack ist deployed"
        docker stack services unityai
    else
        log_warning "✗ Unity AI Stack ist nicht deployed"
    fi
    
    log_substep "Firewall-Status prüfen"
    case $OS in
        ubuntu|debian)
            if ufw status | grep -q "Status: active"; then
                log_info "✓ UFW Firewall ist aktiv"
            else
                log_warning "✗ UFW Firewall ist nicht aktiv"
            fi
            ;;
        centos|rhel|fedora)
            if systemctl is-active --quiet firewalld; then
                log_info "✓ Firewalld ist aktiv"
            else
                log_warning "✗ Firewalld ist nicht aktiv"
            fi
            ;;
    esac
    
    log_success "Gesundheitschecks abgeschlossen"
}

# =============================================================================
# ABSCHLUSSINFORMATIONEN
# =============================================================================
show_completion_info() {
    log_step "Setup abgeschlossen!"
    
    echo
    echo "${GREEN}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo "${GREEN}║                        UNITY AI SETUP ABGESCHLOSSEN                         ║${NC}"
    echo "${GREEN}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo
    
    log_info "📋 Setup-Zusammenfassung:"
    echo "  ✓ System aktualisiert und gehärtet"
    echo "  ✓ Docker und Docker Compose installiert"
    echo "  ✓ Firewall konfiguriert"
    echo "  ✓ Fail2Ban eingerichtet"
    echo "  ✓ Unity AI Benutzer und Verzeichnisse erstellt"
    echo "  ✓ Projekt deployed"
    echo "  ✓ Docker Swarm eingerichtet"
    echo "  ✓ Monitoring und Logging konfiguriert"
    echo "  ✓ Backup-System eingerichtet"
    echo "  ✓ System optimiert"
    echo
    
    log_info "🌐 Zugriffs-URLs (nach DNS-Konfiguration):"
    echo "  • API: https://api.unit-y-ai.io"
    echo "  • n8n: https://n8n.unit-y-ai.io"
    echo "  • Traefik Dashboard: https://traefik.unit-y-ai.io"
    echo
    
    log_info "🔧 Nützliche Befehle:"
    echo "  • Stack Status: docker stack services unityai"
    echo "  • Service Logs: docker service logs unityai_<service_name>"
    echo "  • Stack neustarten: systemctl restart unityai"
    echo "  • Backup ausführen: /opt/unityai/scripts/backup.sh"
    echo "  • Logs anzeigen: tail -f /var/log/unityai/*.log"
    echo
    
    log_info "📁 Wichtige Verzeichnisse:"
    echo "  • Projekt: /opt/unityai"
    echo "  • Logs: /var/log/unityai"
    echo "  • Backups: /opt/unityai/backups"
    echo "  • Konfiguration: /opt/unityai/config"
    echo
    
    log_warning "⚠️  Nächste Schritte:"
    echo "  1. DNS-Einträge für Ihre Domain konfigurieren"
    echo "  2. SSL-Zertifikate über Let's Encrypt werden automatisch erstellt"
    echo "  3. Secrets in /opt/unityai/config/secrets.env konfigurieren"
    echo "  4. API-Keys und Passwörter anpassen"
    echo "  5. Backup-Strategie testen"
    echo
    
    log_success "Unity AI Platform ist bereit für den Produktionseinsatz!"
    echo "Log-Datei: $LOG_FILE"
}

# =============================================================================
# HAUPTFUNKTION
# =============================================================================
main() {
    echo "${BLUE}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo "${BLUE}║                    UNITY AI COMPLETE SERVER SETUP                           ║${NC}"
    echo "${BLUE}║                         Vollständige Server-Einrichtung                     ║${NC}"
    echo "${BLUE}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo
    
    # Vorbereitungen
    check_lock
    check_root
    detect_os
    
    # Setup-Schritte
    update_system
    install_docker
    install_docker_compose
    configure_firewall
    configure_fail2ban
    setup_user_and_directories
    deploy_project
    setup_docker_swarm
    setup_monitoring
    setup_backup
    optimize_system
    
    # Abschluss
    run_health_checks
    show_completion_info
    
    log_success "Setup erfolgreich abgeschlossen!"
}

# Skript ausführen
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi