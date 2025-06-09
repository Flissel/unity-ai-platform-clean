1️⃣ Externe Schicht
Internet → Traefik

Let’s Encrypt per DNS‐Challenge (Cloudflare-Token) eingerichtet

SSL/TLS-Termination, Redirect von HTTP auf HTTPS

Rate-Limiting & Basic-Auth-Middleware konfiguriert

Check: DNS-Einträge auf *.unit-y-ai.io, Traefik-Dashboard erreichbar über Port 443.

2️⃣ Reverse Proxy & Load Balancing
Traefik in Docker Swarm

Overlay-Netzwerk unityai-network

Labels auf jedem Service (Host(), entrypoints=websecure, certresolver=letsencrypt)

Dynamische dynamic.yml für Header (HSTS, CSP, X-Frame-Options)

Check:

docker service logs unityai-traefik show keine SSL-Errors

Middleware „security-headers“ aktiv.

3️⃣ Application Services
Unity AI App (FastAPI)

Built via Dockerfile, in GHCR getaggt

ENV aus .env.fastapi + .env.security

Healthcheck /health

n8n Core

Queue-Mode aktiviert (EXECUTIONS_MODE=queue)

ENV aus n8n/env/.env.*

Basic-Auth + Encryption-Key aus Docker-Secrets

Health-Endpoint /healthz

n8n Worker (BullMQ) oder External Task-Runner

runner-launcher im external mode (n8n runner)

Auth-Token + Redis-PW aus Secrets

Skalierbar via docker service scale

Python Worker (optional für ML-Skripte)

Läuft im selben Overlay-Netz

Zugriff auf gemeinsame Libraries (common_libs)

Check:

Jeder Container loggt „Started“ bzw. „Runner broker connected“.

Intern verwenden Services http://n8n:5678, redis, db als Hostnamen.

4️⃣ Shared Scripts & Libraries
Deine Scripts/Libs (Data Processing, ML-Inference, Scraping, etc.) landen in einem common volume oder im Docker-Image.

Whitelisted in .env.nodes und in deinem Dockerfile vorinstalliert.

Check:

docker exec unityai-n8n_worker pip list zeigt pandas, numpy etc.

NODE_FUNCTION_ALLOW_EXTERNAL deckt alle nötigen Pakete ab.

5️⃣ Data & Queue Layer
PostgreSQL

Datenbank n8n, User n8n_user, Passwort aus Secret pg_pw

Volume postgres-data

Migrationen durch n8n beim Start → Tabellen angelegt

Redis

Passwort aus Secret redis_pw

Append-only‐Log aktiviert

Nutzt Redis für Queue (BullMQ), Sessions und Caching

Docker Volumes

n8n-data, redis-data, postgres-data, logs, uploads

Check:

docker service logs unityai-db kein Crash

docker exec redis redis-cli -a <PW> ping → PONG

6️⃣ Monitoring & Observability




Central Logs (optional ELK/Fluentd)

Logs aller Services in ein Aggregations-Volume oder externen Stack

Check:

https://metrics.unit-y-ai.io/targets → alle Targets UP



7️⃣ Security & Configuration
Docker Secrets für alle sensitiven Werte:
pg_pw, n8n_admin_password, n8n_encryption_key, redis_pw, runner_token, (optional openai_key)

.env.*-Files versioniert im Git, nur Platzhalter oder _FILE-Referenzen

Basic-Auth aktiviert in n8n, Secure-Cookies, CORS-Whitelist

Check:

docker secret ls zeigt alle notwendigen Secrets

curl -I https://n8n.unit-y-ai.io → 401 ohne Auth, 200 mit.

8️⃣ Netzwerk
Overlay-Network unityai-network verbindet alle Services

Interner DNS-Service: n8n, db, redis, app, runner-launcher

Check:

docker network inspect unityai-network zeigt alle Container als Endpoints.

ping n8n von app-Container funktioniert intern.

9️⃣ CI/CD & GitOps („ohne Enterprise“)
Build-Workflow

Baue & pushe n8n + FastAPI nach GHCR mit Tags ${GITHUB_SHA}, latest.

Deploy-Workflow

Bei Erfolg → SSH zum VPS → docker stack deploy mit IMAGE_TAG.

Workflow Export/Import

Skripte scripts/export-dev.sh, scripts/import-prod.sh für _tested-Workflows

Check:

GitHub Actions: beide Workflows laufen fehlerfrei durch.

Prod-Stack aktualisiert sich automatisch bei jedem Merge in main.

🎯 Zusammenfassung
Diese Architektur und die dazugehörige Checkliste sorgen dafür, dass du:

Skalierbar und hochverfügbar im Swarm-Cluster bist

Sicher alle Passwörter und Keys per Docker Secrets verwaltest

Modular per .env.* konfigurierst und leicht erweiterst

Beobachtbar mit Monitoring arbeitest

Automatisiert via GitHub Actions buildest und deployst

Versioniert deine n8n-Workflows ohne Enterprise-Feature