# UnityAI - Template-basierte Konfiguration

Für Benutzer, die bereits ihre Umgebungsvariablen kennen und eine schnelle, nicht-interaktive Konfiguration bevorzugen.

## Schnelle Einrichtung

### 1. Template kopieren
```powershell
# Kopiere das Template
copy config\production-config-template.env config\production-config.env
```

### 2. Konfiguration ausfüllen
Öffne `config\production-config.env` in einem Texteditor und fülle deine Werte ein:

**Wichtige Felder (mindestens erforderlich):**
- `DOMAIN` - Deine Produktions-Domain
- `POSTGRES_PASSWORD` - Sicheres Datenbank-Passwort
- `REDIS_PASSWORD` - Redis Passwort
- `JWT_SECRET_KEY` - JWT Secret (min. 32 Zeichen)
- `N8N_BASIC_AUTH_PASSWORD` - N8N Admin Passwort
- `N8N_ENCRYPTION_KEY` - N8N Verschlüsselungsschlüssel

**Beispiel:**
```env
DOMAIN=unityai.meinefirma.de
SSL_ENABLED=true
POSTGRES_PASSWORD=MeinSicheresDBPasswort123!
REDIS_PASSWORD=MeinRedisPasswort456!
JWT_SECRET_KEY=mein-super-sicherer-jwt-schluessel-mit-32-zeichen
N8N_BASIC_AUTH_PASSWORD=MeinN8NPasswort789!
```

### 3. Deployment starten
```powershell
# Führe das One-Click-Skript aus
.\scripts\one-click-production.ps1
```

## Vorteile der Template-Methode

✅ **Schnell** - Keine interaktiven Eingaben erforderlich
✅ **Wiederholbar** - Template kann für mehrere Deployments verwendet werden
✅ **Versionskontrolle** - Konfiguration kann in Git verwaltet werden (ohne Secrets)
✅ **Automatisierung** - Ideal für CI/CD Pipelines
✅ **Backup** - Konfiguration ist als Datei gesichert

## Sicherheitshinweise

⚠️ **Wichtig:**
- Füge `config/production-config.env` zu `.gitignore` hinzu
- Verwende starke, einzigartige Passwörter
- Teile die ausgefüllte Konfigurationsdatei niemals öffentlich
- Erstelle Backups deiner Konfiguration an sicheren Orten

## Template-Struktur

Das Template ist in Kategorien unterteilt:

1. **Basic Configuration** - Domain, SSL, Environment
2. **Database Configuration** - PostgreSQL Einstellungen
3. **Redis Configuration** - Cache-Einstellungen
4. **Security Configuration** - API Keys, JWT, Sessions
5. **N8N Configuration** - Workflow-Engine Einstellungen
6. **Email Configuration** - SMTP für Benachrichtigungen
7. **External API Keys** - OpenAI, Google, Slack, etc.
8. **Monitoring & Logging** - Logs und Error Tracking
9. **Advanced Configuration** - Worker, Rate Limiting
10. **Docker Swarm Configuration** - Cluster-Einstellungen
11. **Backup Configuration** - Automatische Backups

## Fallback zur interaktiven Konfiguration

Wenn du das Template nicht verwenden möchtest, bietet das Skript automatisch die interaktive Konfiguration an:

```
Use interactive configuration instead? (y/N)
```

Gib `y` ein, um zur gewohnten interaktiven Eingabe zu wechseln.

## Fehlerbehebung

**Problem:** Skript findet Template nicht
**Lösung:** Stelle sicher, dass du im UnityAI Hauptverzeichnis bist

**Problem:** Konfiguration wird nicht geladen
**Lösung:** Überprüfe, ob `config/production-config.env` existiert und ausgefüllt ist

**Problem:** Deployment schlägt fehl
**Lösung:** Überprüfe die Logs und stelle sicher, dass alle erforderlichen Felder ausgefüllt sind