# Unity AI System - Konfigurationstemplate

> **Anleitung**: Fülle alle Felder aus und verwende diese Informationen für die Systemkonfiguration.

## 🏢 **Server-Informationen**

### Deployment-Umgebung
- **Server-Typ**: [ ] Lokaler Server [ ] Cloud (AWS/Azure/GCP) [ ] VPS [ ] Andere: ___________
- **Betriebssystem**: [ ] Linux (Ubuntu/Debian) [ ] Windows Server [ ] macOS [ ] Andere: ___________
- **IP-Adresse/Domain**: ___________________________________________
- **SSH-Zugang**: Benutzername: _____________ Port: _____________

### SSL/HTTPS
- **Domain für SSL**: ___________________________________________
- **SSL-Zertifikat vorhanden**: [ ] Ja [ ] Nein (wird automatisch erstellt)
- **E-Mail für Let's Encrypt**: ___________________________________________

## 🔑 **API-Schlüssel und Zugangsdaten**

### OpenAI (für AutoGen)
- **OpenAI API Key**: ___________________________________________
- **OpenAI Organization ID** (optional): ___________________________________________

### n8n
- **n8n API Key**: ___________________________________________
  > *Hinweis: Wird nach der Installation generiert*

### Weitere Services (optional)
- **Slack Bot Token**: ___________________________________________
- **Discord Bot Token**: ___________________________________________
- **Telegram Bot Token**: ___________________________________________
- **Email SMTP**:
  - Server: ___________________________________________
  - Port: ___________________________________________
  - Benutzername: ___________________________________________
  - Passwort: ___________________________________________

## 🗄️ **Datenbank-Konfiguration**

### PostgreSQL
- **Datenbank-Name**: ___________________________________________
- **Benutzername**: ___________________________________________
- **Passwort**: ___________________________________________
- **Host**: ___________________________________________
- **Port**: ___________________________________________

### Redis (für Caching)
- **Redis Host**: ___________________________________________
- **Redis Port**: ___________________________________________
- **Redis Passwort** (optional): ___________________________________________

## 🔐 **Sicherheitseinstellungen**

### Authentifizierung
- **n8n Admin Benutzername**: ___________________________________________
- **n8n Admin Passwort**: ___________________________________________
- **FastAPI Admin Token**: ___________________________________________

### Verschlüsselung
- **Encryption Key** (32 Zeichen): ___________________________________________
- **JWT Secret**: ___________________________________________

## 🌐 **Netzwerk-Konfiguration**

### Ports
- **FastAPI Port**: [ ] 8000 (Standard) [ ] Andere: ___________
- **n8n Port**: [ ] 5678 (Standard) [ ] Andere: ___________
- **Traefik HTTP Port**: [ ] 80 (Standard) [ ] Andere: ___________
- **Traefik HTTPS Port**: [ ] 443 (Standard) [ ] Andere: ___________

### Firewall
- **Zusätzliche erlaubte IPs**: ___________________________________________
- **VPN-Zugang erforderlich**: [ ] Ja [ ] Nein

## 📊 **Monitoring und Logging**

### Prometheus/Grafana
- **Monitoring aktivieren**: [ ] Ja [ ] Nein
- **Grafana Admin Passwort**: ___________________________________________

### Log-Level
- **FastAPI Log-Level**: [ ] DEBUG [ ] INFO [ ] WARNING [ ] ERROR
- **n8n Log-Level**: [ ] DEBUG [ ] INFO [ ] WARNING [ ] ERROR

## 💾 **Backup-Konfiguration**

### Automatische Backups
- **Backup aktivieren**: [ ] Ja [ ] Nein
- **Backup-Intervall**: [ ] Täglich [ ] Wöchentlich [ ] Monatlich
- **Backup-Speicherort**: ___________________________________________
- **Anzahl Backups behalten**: ___________________________________________

### Cloud-Backup (optional)
- **Cloud-Provider**: [ ] AWS S3 [ ] Azure Blob [ ] Google Cloud [ ] Andere: ___________
- **Bucket/Container Name**: ___________________________________________
- **Access Key**: ___________________________________________
- **Secret Key**: ___________________________________________

## 🚀 **Deployment-Präferenzen**

### Installation
- **Installationsmethode**: [ ] Automatisch (setup-server.sh/.ps1) [ ] Manuell
- **Docker Swarm verwenden**: [ ] Ja [ ] Nein
- **Entwicklungsmodus**: [ ] Ja [ ] Nein

### Skalierung
- **Erwartete Benutzeranzahl**: ___________________________________________
- **Erwartete Workflow-Ausführungen/Tag**: ___________________________________________
- **Ressourcen-Limits setzen**: [ ] Ja [ ] Nein

## 📝 **Zusätzliche Konfiguration**

### Zeitzone
- **Server-Zeitzone**: ___________________________________________

### Sprache
- **Standard-Sprache**: [ ] Deutsch [ ] Englisch [ ] Andere: ___________

### Custom Workflows
- **Eigene Workflows vorhanden**: [ ] Ja [ ] Nein
- **Workflow-Dateien Pfad**: ___________________________________________

## ✅ **Checkliste vor Deployment**

- [ ] Alle erforderlichen Felder ausgefüllt
- [ ] API-Schlüssel getestet
- [ ] Server-Zugang verifiziert
- [ ] Domain/DNS konfiguriert
- [ ] Firewall-Regeln geplant
- [ ] Backup-Strategie definiert
- [ ] SSL-Zertifikat vorbereitet
- [ ] Monitoring-Tools ausgewählt

---

## 🔧 **Nächste Schritte nach dem Ausfüllen**

1. **Automatische Konfiguration**:
   ```bash
   # Linux/macOS
   ./scripts/setup-server.sh
   
   # Windows
   .\scripts\setup-server.ps1
   ```

2. **Manuelle Konfiguration**:
   - Folge der `DEPLOYMENT-GUIDE.md`
   - Verwende die `SETUP-CHECKLIST.md`

3. **Umgebungsvariablen setzen**:
   - Bearbeite die `.env.*` Dateien mit deinen Werten
   - Verwende `generate_envs.py` für automatische Generierung

4. **System starten**:
   ```bash
   docker-compose up -d
   ```

5. **Workflows importieren**:
   ```bash
   # Linux/macOS
   ./scripts/import-workflows.sh
   
   # Windows
   .\scripts\import-workflows.ps1
   ```

---

**📞 Support**: Bei Fragen oder Problemen, siehe `README.md` oder erstelle ein Issue im Repository.