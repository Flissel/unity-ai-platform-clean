# Unity AI Platform - Complete Server Setup

## 🚀 Vollständige Server-Einrichtung

Dieses Verzeichnis enthält alle notwendigen Skripte für die komplette Einrichtung eines Unity AI Servers auf Linux.

## 📋 Übersicht der Skripte

### 🎯 **setup-server-complete.sh** - Master Setup Script
**Das Haupt-Skript für die komplette Server-Einrichtung**

```bash
sudo bash scripts/setup-server-complete.sh
```

**Was es macht:**
- ✅ System-Updates und Sicherheitshärtung
- ✅ Docker & Docker Compose Installation
- ✅ Firewall-Konfiguration (UFW/Firewalld)
- ✅ Fail2Ban Einrichtung
- ✅ Benutzer und Verzeichnisse erstellen
- ✅ Unity AI Projekt deployment
- ✅ Docker Swarm Setup
- ✅ Monitoring und Logging
- ✅ Backup-System
- ✅ System-Optimierung
- ✅ Gesundheitschecks

### 🔐 **setup-docker-secrets.sh** - Secrets Management
**Erstellt und verwaltet alle Docker Secrets**

```bash
bash scripts/setup-docker-secrets.sh
```

### 🐳 **deploy-swarm.sh** - Docker Swarm Deployment
**Deployt die Unity AI Anwendung in Docker Swarm**

```bash
bash scripts/deploy-swarm.sh
```

### 🏭 **setup-production.sh** - Produktions-Setup
**Interaktive Produktions-Konfiguration**

```bash
bash scripts/setup-production.sh
```

### 💻 **setup-env.ps1** - Windows Development Setup
**PowerShell-Skript für lokale Windows-Entwicklung**

```powershell
.\scripts\setup-env.ps1
```

## 🛠️ Schnellstart - Komplette Server-Einrichtung

### Voraussetzungen
- ✅ Frischer Linux Server (Ubuntu 20.04+, Debian 11+, CentOS 8+, RHEL 8+)
- ✅ Root-Zugriff (sudo)
- ✅ Internetverbindung
- ✅ Domain mit DNS-Zugriff
- ✅ Cloudflare Account (für SSL)

### 1. Repository klonen
```bash
git clone https://github.com/your-org/unityai.git
cd unityai
```

### 2. Master Setup ausführen
```bash
sudo bash scripts/setup-server-complete.sh
```

### 3. Konfiguration anpassen
```bash
# Secrets konfigurieren
sudo nano /opt/unityai/config/secrets.env

# Umgebungsvariablen anpassen
sudo nano /opt/unityai/config/.env.production
```

### 4. DNS konfigurieren
Erstelle folgende DNS-Einträge:
```
api.unit-y-ai.io     A    YOUR_SERVER_IP
n8n.unit-y-ai.io     A    YOUR_SERVER_IP
traefik.unit-y-ai.io A    YOUR_SERVER_IP
```

### 5. Services starten
```bash
sudo systemctl start unityai
sudo systemctl status unityai
```

## 📊 Status und Monitoring

### Service Status prüfen
```bash
# Docker Stack Status
docker stack services unityai

# Service Logs
docker service logs unityai_app
docker service logs unityai_n8n
docker service logs unityai_traefik

# System Status
sudo systemctl status unityai
```

### Logs anzeigen
```bash
# Unity AI Logs
tail -f /var/log/unityai/*.log

# Setup Log
tail -f /var/log/unityai-complete-setup-*.log

# Docker Logs
docker service logs -f unityai_app
```

## 🔧 Wartung und Administration

### Backup ausführen
```bash
# Manuelles Backup
/opt/unityai/scripts/backup.sh

# Backup-Status prüfen
ls -la /opt/unityai/backups/
```

### Services neustarten
```bash
# Kompletter Stack
sudo systemctl restart unityai

# Einzelner Service
docker service update --force unityai_app
```

### Updates durchführen
```bash
# Code aktualisieren
cd /opt/unityai
git pull

# Services neu deployen
bash scripts/deploy-swarm.sh
```

## 🔐 Sicherheit

### Firewall Status
```bash
# Ubuntu/Debian
sudo ufw status

# CentOS/RHEL
sudo firewall-cmd --list-all
```

### Fail2Ban Status
```bash
sudo fail2ban-client status
sudo fail2ban-client status sshd
```

### SSL-Zertifikate
```bash
# Traefik verwaltet SSL automatisch über Let's Encrypt
# Zertifikat-Status in Traefik Dashboard prüfen
```

## 🌐 Zugriffs-URLs

Nach erfolgreichem Setup sind folgende Services verfügbar:

- **🔗 API**: https://api.unit-y-ai.io
- **🔄 n8n**: https://n8n.unit-y-ai.io
- **📊 Traefik Dashboard**: https://traefik.unit-y-ai.io

## 📁 Verzeichnisstruktur

```
/opt/unityai/
├── compose/                 # Docker Compose Dateien
├── config/                  # Konfigurationsdateien
│   ├── .env.production     # Produktions-Umgebungsvariablen
│   └── secrets.env         # Secrets (nicht in Git!)
├── scripts/                # Setup und Wartungsskripte
├── data/                   # Persistente Daten
├── logs/                   # Anwendungslogs
├── uploads/                # Datei-Uploads
└── backups/                # Backup-Dateien

/var/log/unityai/           # System-Logs
```

## 🚨 Troubleshooting

### Services starten nicht
```bash
# Docker Status prüfen
sudo systemctl status docker

# Swarm Status prüfen
docker info | grep Swarm

# Service-Details anzeigen
docker service ps unityai_app --no-trunc
```

### SSL-Probleme
```bash
# Traefik Logs prüfen
docker service logs unityai_traefik

# DNS-Auflösung testen
nslookup api.unit-y-ai.io
```

### Performance-Probleme
```bash
# Ressourcen-Verbrauch
docker stats

# System-Ressourcen
htop
df -h
```

## 📞 Support

### Log-Sammlung für Support
```bash
# Alle relevanten Logs sammeln
tar czf unityai-logs-$(date +%Y%m%d).tar.gz \
    /var/log/unityai/ \
    /opt/unityai/logs/ \
    /var/log/docker.log
```

### Häufige Probleme

1. **Services zeigen 0/1 Replicas**
   - Node-Labels prüfen: `docker node ls`
   - Constraints prüfen: `docker service inspect unityai_app`

2. **SSL-Zertifikate werden nicht erstellt**
   - DNS-Einträge prüfen
   - Cloudflare-Konfiguration überprüfen
   - Traefik-Logs analysieren

3. **Datenbank-Verbindungsfehler**
   - PostgreSQL-Service Status prüfen
   - Secrets validieren
   - Netzwerk-Konnektivität testen

## 🔄 Automatisierung

### Cron-Jobs
Das Setup erstellt automatisch folgende Cron-Jobs:

```bash
# Tägliche Backups um 2:00 Uhr
0 2 * * * /opt/unityai/scripts/backup.sh

# Cron-Jobs anzeigen
crontab -u unityai -l
```

### Systemd Services
```bash
# Unity AI Service
sudo systemctl enable unityai
sudo systemctl start unityai

# Service-Status
sudo systemctl status unityai
```

---

## 📝 Changelog

### Version 1.0.0
- ✅ Initiale Version des Complete Setup Scripts
- ✅ Vollständige Docker Swarm Integration
- ✅ Automatische SSL-Zertifikat-Verwaltung
- ✅ Backup und Monitoring System
- ✅ Multi-OS Support (Ubuntu, Debian, CentOS, RHEL)

---

**🎉 Unity AI Platform - Bereit für die Produktion!**