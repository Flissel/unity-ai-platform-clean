# Domino-Automation Platform v0.1  
Single-Server Edition – Traefik • n8n (Queue) • FastAPI • Autogen 0.4.x

---

## 1  Zielsetzung

| ✔ | Funktion |
|---|-----------|
| **Empfängt** | Chat- / Webhook-Events (Slack, WhatsApp, Web-UI) |
| **Plant** | Autogen-Agents (Topics) interpretieren das Anliegen, erzeugen / starten Workflows |
| **Orchestriert** | FastAPI importiert / aktualisiert Workflows via n8n-REST / CLI |
| **Ausführt** | n8n (Queue-Mode + Worker) erledigt deterministische Schritte |
| **Lernt** | Ergebnisse fließen auf einen Redis-Stream; Agents stoßen Domino-Folgeschritte an |
| **Antwortet** | Notifier schickt Outcome zurück in Chat / UI |

---

## 2  High-Level-Architektur

```mermaid
graph TD
A(Chat/Webhook)-->B(Autogen Topics)
B--plan-->C(FastAPI /decide)
C--import/run-->D[n8n API]
D--jobs-->E[n8n Workers]
E--result-->F(Redis Stream)
F-->B
F-->G(Notifier)-->A
3 Tech-Stack
Layer	Tool	Key-Feature
Reverse-Proxy	Traefik v2	Auto-Routes per Docker-Label, ACME TLS
Orchestration	Docker Compose v3.9	Ein-Server-Deployment, später Swarm / K8s-ready
State	Postgres 15 (Workflows) • Redis 7 (Queue + Streams)	
Workflow Engine	n8n 1.x („queue“ Mode)	
Agent Layer	Autogen 0.4.x (Topic-Subscription)	
API Bridge	FastAPI + Uvicorn	
Python ML	Custom n8n-Image (pandas, numpy, scikit-learn)	
Observability	Prometheus, Grafana, Traefik-Dashboard	
Secrets	Docker Secrets, _FILE-Variablen	
Security	SSH-Keys, UFW 443-only, n8n Basic-Auth	

4 Repository-Layout (Top-Level)
bash
Kopieren
Bearbeiten
root/
├─ compose/docker-compose.yml      # Gesamt-Stack
├─ traefik/acme.json               # LE-Storage
├─ n8n/
│  ├─ Dockerfile                   # +Python-Libs
│  └─ env/ .env.*                  # modulare ENV-Blöcke
├─ fastapi/
│  ├─ app.py                       # /decide /callback /topics
│  └─ requirements.txt
├─ scripts/                        # Python Worker-Skripte
├─ docs/architecture.md
└─ generate_envs.py                # erzeugt alle .env-Files
5 Compose-Ausschnitt (Kernelemente)
yaml
Kopieren
Bearbeiten
version: "3.9"
services:
  traefik:
    image: traefik:v2.11
    command:
      - --providers.docker=true
      - --entrypoints.websecure.address=:443
      - --certificatesresolvers.le.acme.dnschallenge=true
      - --certificatesresolvers.le.acme.dnschallenge.provider=cloudflare
      - --certificatesresolvers.le.acme.email=ops@unit-y.ai
      - --certificatesresolvers.le.acme.storage=/acme/acme.json
    environment:
      - CF_DNS_API_TOKEN=${CF_DNS_API_TOKEN}
    ports: ["443:443"]
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./traefik/acme.json:/acme/acme.json
    networks: [core]

  redis:
    image: redis:7-alpine
    networks: [core]

  postgres:
    image: postgres:15
    env_file: [n8n/env/.env.database]
    volumes: [pgdata:/var/lib/postgresql/data]
    networks: [core]

  n8n:
    build: ./n8n
    env_file:
      - n8n/env/.env.common
      - n8n/env/.env.queue
      - n8n/env/.env.nodes
      - n8n/env/.env.deployment
    labels:
      - traefik.http.routers.n8n.rule=Host(`n8n.unit-y-ai.io`)
      - traefik.http.routers.n8n.entrypoints=websecure
      - traefik.http.routers.n8n.tls.certresolver=le
    depends_on: [redis, postgres]
    networks: [core]

  n8n-worker:
    image: n8n
    command: n8n worker
    env_file: [n8n/env/.env.queue]
    depends_on: [redis, postgres]
    networks: [core]

  fastapi:
    build: ./fastapi
    env_file: [.env.fastapi]
    labels:
      - traefik.http.routers.api.rule=Host(`api.unit-y-ai.io`)
      - traefik.http.routers.api.entrypoints=websecure
      - traefik.http.routers.api.tls.certresolver=le
    depends_on: [redis, n8n]
    networks: [core]

volumes:
  pgdata:
networks:
  core:
6 Sicherheits-Checkliste
SSH: Key-Login only, Fail2Ban, unattended-upgrades.

UFW: allow 443/tcp, alles andere deny.

Traefik Basic-Auth für n8n-UI, JWT optional.

Secrets: Passwörter via Docker-Secrets oder _FILE.

User: Container laufen als nicht-root (node), read_only wo möglich.

Backups: pg_dump cron, Redis-RDB, n8n binary data → S3/MinIO.

7 Roadmap (Ein-Server → Multi-Node)
Phase	Trigger	Aktion
0 MVP	< 50 k Runs/Tag	1 × CX11
A IO-Limit	DB > 20 GB	eigene Postgres-VM
B CPU-Peaks	Queue-Lag > 5 s	n8n-worker replicas=3
C SLA 99.9 %	Kundentraffic	zweiter Edge-Node + Keepalived
D Mandanten	DSGVO / SLA	Kunde-pro-VM oder Namespace