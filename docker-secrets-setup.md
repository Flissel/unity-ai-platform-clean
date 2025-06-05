# Docker Secrets Setup für n8n

## Übersicht
Die .env-Dateien verwenden jetzt Docker Secrets für sensible Daten (Best Practice).

## 1. Secrets erstellen

### PostgreSQL Passwort
```bash
# Starkes 32-Zeichen Hex-Passwort generieren
openssl rand -hex 32 > pg_password.txt

# Docker Secret erstellen
docker secret create pg_pw pg_password.txt

# Temporäre Datei löschen
rm pg_password.txt
```

### n8n Basic Auth Passwort
```bash
# Starkes Passwort generieren
openssl rand -base64 32 > n8n_password.txt

# Docker Secret erstellen
docker secret create n8n_pw n8n_password.txt

# Temporäre Datei löschen
rm n8n_password.txt
```

## 2. Docker Compose anpassen

Fügen Sie zu Ihrer `docker-compose.yml` hinzu:

```yaml
version: "3.9"

secrets:
  pg_pw:
    external: true
  n8n_pw:
    external: true

services:
  postgres:
    image: postgres:15
    env_file: [n8n/env/.env.database]
    secrets:
      - pg_pw
    volumes: [pgdata:/var/lib/postgresql/data]
    networks: [core]

  n8n:
    build: ./n8n
    env_file:
      - n8n/env/.env.common
      - n8n/env/.env.queue
      - n8n/env/.env.nodes
      - n8n/env/.env.deployment
      - n8n/env/.env.security
    secrets:
      - n8n_pw
      - pg_pw
    # ... rest der Konfiguration
```

## 3. Secrets anzeigen (für Debugging)

```bash
# Alle Secrets auflisten
docker secret ls

# Secret-Inhalt anzeigen (nur für Debugging!)
docker secret inspect pg_pw
```

## 4. Fallback ohne Docker Secrets

Falls Sie Docker Secrets nicht verwenden möchten, ändern Sie in den .env-Dateien:

```bash
# Statt:
DB_POSTGRESDB_PASSWORD_FILE=/run/secrets/pg_pw

# Verwenden Sie:
DB_POSTGRESDB_PASSWORD=ihr-starkes-passwort-hier
```

⚠️ **Sicherheitshinweis**: Verwenden Sie Docker Secrets in der Produktion!