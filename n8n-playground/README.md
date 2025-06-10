# n8n API Playground

> Comprehensive n8n API integration and workflow automation platform for UnityAI

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 🎯 Überblick

Der n8n API Playground ist eine modulare, erweiterbare Plattform für die Integration von n8n-Workflows in UnityAI-Anwendungen. Das System bietet eine umfassende API-Schnittstelle, Workflow-Automatisierung, Benutzer-Management und Monitoring-Funktionen.

### 🌟 Hauptfunktionen

- **🔄 Workflow-Automatisierung**: Teste und verwalte n8n-Workflows programmatisch
- **🚀 FastAPI Integration**: Nahtlose Verbindung zwischen n8n und deiner eigenen API
- **📊 Monitoring**: Überwache Workflow-Status und Performance in Echtzeit
- **👥 Benutzer-Management**: Automatisierte Benutzerregistrierung und Authentifizierung
- **🔧 Modulares Design**: Erweiterbare Architektur für zukünftige Anforderungen
- **🐳 Docker Support**: Vollständige Containerisierung für einfache Bereitstellung

## 🏗️ Architektur

```
n8n-playground/
├── core/                    # Kern-Framework
│   ├── __init__.py
│   ├── playground_manager.py
│   ├── api_client.py
│   ├── workflow_executor.py
│   ├── response_handler.py
│   └── exceptions.py
├── modules/                 # Modulare Komponenten
│   ├── workflow_automation/ # Workflow-Management
│   ├── fastapi_integration/ # API-Integration
│   ├── monitoring/         # Überwachung & Metriken
│   └── user_management/    # Benutzer-Verwaltung
├── templates/              # Workflow-Vorlagen
├── data/                   # Datenbank & Logs
├── static/                 # Statische Dateien
├── tests/                  # Test-Suite
└── docs/                   # Dokumentation
```

## 🚀 Schnellstart

### Voraussetzungen

- Python 3.9+
- Docker & Docker Compose (optional)
- n8n-Instanz (lokal oder remote)
- PostgreSQL (optional, SQLite als Standard)
- Redis (optional, Memory-Cache als Standard)

### 1. Repository klonen

```bash
git clone https://github.com/unityai/n8n-playground.git
cd n8n-playground
```

### 2. Umgebung einrichten

```bash
# Python Virtual Environment erstellen
python -m venv venv

# Virtual Environment aktivieren
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Dependencies installieren
pip install -r requirements.txt

# Development Dependencies (optional)
pip install -r requirements-dev.txt
```

### 3. Konfiguration

```bash
# Umgebungsvariablen kopieren und anpassen
cp .env.example .env

# .env Datei bearbeiten
# Mindestens N8N_API_BASE_URL und Authentifizierung konfigurieren
```

### 4. Datenbank initialisieren

```bash
# Datenbank-Migrationen ausführen
alembic upgrade head
```

### 5. Anwendung starten

```bash
# Development Server
python main.py

# Oder mit Uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

### 6. API erkunden

Öffne deinen Browser und navigiere zu:

- **API Dokumentation**: http://localhost:8080/docs
- **Alternative Docs**: http://localhost:8080/redoc
- **Health Check**: http://localhost:8080/health

## 🐳 Docker Deployment

### Development Environment

```bash
# Alle Services starten
docker-compose -f docker-compose.dev.yml up -d

# Logs verfolgen
docker-compose -f docker-compose.dev.yml logs -f

# Services stoppen
docker-compose -f docker-compose.dev.yml down
```

### Production Deployment

```bash
# Production Build
docker build -f Dockerfile.prod -t n8n-playground:latest .

# Mit Docker Compose
docker-compose -f docker-compose.prod.yml up -d
```

## 📚 Module

### 🔄 Workflow Automation

Verwalte und automatisiere n8n-Workflows:

```python
from modules.workflow_automation import WorkflowManager

# Workflow Manager initialisieren
manager = WorkflowManager()

# Workflow erstellen
workflow = await manager.create_workflow(
    name="Test Workflow",
    template="basic_http_request",
    parameters={"url": "https://api.example.com"}
)

# Workflow ausführen
execution = await manager.execute_workflow(workflow.id)
```

**API Endpoints:**
- `POST /workflow-automation/workflows` - Workflow erstellen
- `GET /workflow-automation/workflows` - Workflows auflisten
- `POST /workflow-automation/workflows/{id}/execute` - Workflow ausführen
- `GET /workflow-automation/executions` - Ausführungen verfolgen

### 🔗 n8n Direct Integration

Direkte Integration mit der n8n API für erweiterte Workflow-Kontrolle:

```python
from n8n_integration import N8nIntegrationManager

# n8n Integration Manager initialisieren
n8n_manager = N8nIntegrationManager()

# Workflows von n8n abrufen
workflows = await n8n_manager.list_workflows()

# Workflow direkt ausführen
execution = await n8n_manager.execute_workflow(
    workflow_id="123",
    input_data={"param1": "value1"},
    wait_for_completion=True
)

# Ausführungsstatus prüfen
status = await n8n_manager.get_execution_status(execution.id)
```

**n8n API Endpoints:**
- `GET /workflow-automation/n8n/health` - n8n Gesundheitsstatus
- `GET /workflow-automation/n8n/workflows` - n8n Workflows auflisten
- `GET /workflow-automation/n8n/workflows/{id}` - Workflow-Details abrufen
- `POST /workflow-automation/n8n/workflows/{id}/execute` - Workflow ausführen
- `POST /workflow-automation/n8n/workflows/batch-execute` - Batch-Ausführung
- `GET /workflow-automation/n8n/executions/{id}` - Ausführungsstatus
- `DELETE /workflow-automation/n8n/executions/{id}` - Ausführung abbrechen
- `GET /workflow-automation/n8n/executions` - Ausführungen auflisten
- `GET /workflow-automation/n8n/workflows/statistics` - Workflow-Statistiken

### 🚀 FastAPI Integration

Verbinde n8n mit deiner FastAPI-Anwendung:

```python
from modules.fastapi_integration import WebhookManager

# Webhook registrieren
webhook = await webhook_manager.register_webhook(
    workflow_id="workflow_123",
    endpoint="/webhooks/data-processing",
    method="POST"
)
```

**Features:**
- Webhook-Management
- API-Proxy für n8n
- Request/Response-Transformation
- Rate Limiting

### 📊 Monitoring

Überwache System-Performance und Workflow-Status:

```python
from modules.monitoring import MetricsCollector

# Metriken sammeln
metrics = await metrics_collector.get_workflow_metrics()
print(f"Aktive Workflows: {metrics.active_workflows}")
print(f"Erfolgsrate: {metrics.success_rate}%")
```

**Features:**
- Prometheus-Metriken
- Health Checks
- Performance-Monitoring
- Alerting

### 👥 User Management

Verwalte Benutzer und Authentifizierung:

```python
from modules.user_management import UserManager

# Benutzer registrieren
user = await user_manager.register_user(
    username="testuser",
    email="test@example.com",
    password="secure_password"
)

# Authentifizierung
token = await user_manager.authenticate("testuser", "secure_password")
```

**Features:**
- JWT-basierte Authentifizierung
- Rollen-basierte Autorisierung
- Benutzer-Registrierung
- Session-Management

## 🔧 Konfiguration

### Umgebungsvariablen

Wichtige Konfigurationsoptionen:

```bash
# n8n API
N8N_API_BASE_URL=http://localhost:5678
N8N_API_KEY=your_api_key

# Datenbank
DB_TYPE=postgresql
DB_HOST=localhost
DB_NAME=n8n_playground

# Cache
CACHE_TYPE=redis
CACHE_HOST=localhost

# Sicherheit
SECRET_KEY=your-secret-key
CORS_ORIGINS=*

# Module
MODULE_WORKFLOW_AUTOMATION_ENABLED=true
MODULE_MONITORING_ENABLED=true
```

### Module konfigurieren

Jedes Modul kann individuell konfiguriert werden:

```python
# config.py
class ModuleConfig:
    workflow_automation = {
        "max_concurrent_executions": 10,
        "execution_timeout": 300,
        "retry_attempts": 3
    }
    
    monitoring = {
        "metrics_interval": 30,
        "health_check_timeout": 10
    }
```

## 🧪 Testing

### Test-Suite ausführen

```bash
# Alle Tests
pytest

# Mit Coverage
pytest --cov=. --cov-report=html

# Spezifische Tests
pytest tests/test_workflow_automation.py

# Integration Tests
pytest tests/integration/
```

### Test-Kategorien

- **Unit Tests**: Einzelne Komponenten
- **Integration Tests**: Modul-Interaktionen
- **API Tests**: Endpoint-Funktionalität
- **Performance Tests**: Load Testing

## 📈 Monitoring & Observability

### Prometheus Metriken

Verfügbare Metriken:

- `workflow_executions_total` - Anzahl Workflow-Ausführungen
- `workflow_execution_duration_seconds` - Ausführungszeit
- `api_requests_total` - API-Anfragen
- `active_users_total` - Aktive Benutzer

### Grafana Dashboards

Vorkonfigurierte Dashboards für:

- Workflow-Performance
- API-Metriken
- System-Health
- Benutzer-Aktivität

### Logging

Strukturiertes Logging mit:

- JSON-Format
- Korrelations-IDs
- Performance-Metriken
- Error-Tracking

## 🔒 Sicherheit

### Authentifizierung

- JWT-Token basierte Authentifizierung
- Refresh-Token für langfristige Sessions
- Rate Limiting für API-Endpoints

### Autorisierung

- Rollen-basierte Zugriffskontrolle (RBAC)
- Granulare Berechtigungen
- Workflow-spezifische Zugriffsrechte

### Datenschutz

- Verschlüsselung sensibler Daten
- Sichere Passwort-Hashing
- GDPR-konforme Datenverarbeitung

## 🚀 Deployment

### Production Checklist

- [ ] Umgebungsvariablen konfiguriert
- [ ] Datenbank-Migrationen ausgeführt
- [ ] SSL-Zertifikate installiert
- [ ] Monitoring eingerichtet
- [ ] Backup-Strategie implementiert
- [ ] Load Balancer konfiguriert

### Scaling

```bash
# Horizontale Skalierung
docker-compose up --scale n8n-playground=3

# Mit Kubernetes
kubectl scale deployment n8n-playground --replicas=5
```

## 🤝 Entwicklung

### Code-Qualität

```bash
# Code formatieren
black .

# Imports sortieren
isort .

# Linting
flake8 .

# Type checking
mypy .

# Pre-commit hooks
pre-commit install
```

### Neue Module hinzufügen

1. Modul-Verzeichnis erstellen: `modules/new_module/`
2. `SYSTEM_INSTRUCTIONS.md` erstellen
3. Modul-Klassen implementieren
4. Tests schreiben
5. Dokumentation aktualisieren

### Git Workflow

```bash
# Feature Branch erstellen
git checkout -b feature/new-feature

# Changes committen
git add .
git commit -m "feat: add new feature"

# Pull Request erstellen
git push origin feature/new-feature
```

## 📖 API Dokumentation

### Workflow Management

```http
# Workflow erstellen
POST /workflow-automation/workflows
Content-Type: application/json

{
  "name": "Data Processing",
  "template": "data_transformation",
  "parameters": {
    "input_source": "api",
    "output_format": "json"
  }
}

# Workflow ausführen
POST /workflow-automation/workflows/{id}/execute
Content-Type: application/json

{
  "parameters": {
    "data": {"key": "value"}
  }
}
```

### Webhook Integration

```http
# Webhook registrieren
POST /fastapi-integration/webhooks
Content-Type: application/json

{
  "workflow_id": "workflow_123",
  "endpoint": "/webhooks/process-data",
  "method": "POST",
  "authentication": {
    "type": "bearer",
    "token": "your_token"
  }
}
```

## 🔧 Troubleshooting

### Häufige Probleme

**Problem**: n8n API nicht erreichbar
```bash
# Lösung: Verbindung testen
curl -X GET "http://localhost:5678/api/v1/workflows"
```

**Problem**: Datenbank-Verbindungsfehler
```bash
# Lösung: Datenbank-Status prüfen
docker-compose ps postgres
```

**Problem**: Workflow-Ausführung schlägt fehl
```bash
# Lösung: Logs prüfen
docker-compose logs n8n-playground
```

### Debug-Modus

```bash
# Debug-Logging aktivieren
export LOG_LEVEL=DEBUG
export DEBUG=true

# Anwendung starten
python main.py
```

## 📋 Roadmap

### Version 1.1
- [ ] GraphQL API Support
- [ ] Advanced Workflow Templates
- [ ] Real-time Notifications
- [ ] Enhanced Security Features

### Version 1.2
- [ ] Machine Learning Integration
- [ ] Advanced Analytics
- [ ] Multi-tenant Support
- [ ] Plugin System

### Version 2.0
- [ ] Microservices Architecture
- [ ] Event-driven Architecture
- [ ] Advanced Orchestration
- [ ] Cloud-native Features

## 🤝 Contributing

Wir freuen uns über Beiträge! Bitte lies unsere [Contributing Guidelines](CONTRIBUTING.md) für Details.

### Development Setup

```bash
# Repository forken und klonen
git clone https://github.com/yourusername/n8n-playground.git

# Development Environment einrichten
make setup-dev

# Tests ausführen
make test

# Code-Qualität prüfen
make lint
```

## 📄 Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert. Siehe [LICENSE](LICENSE) für Details.

## 🙏 Danksagungen

- [n8n](https://n8n.io/) für die großartige Workflow-Automatisierung
- [FastAPI](https://fastapi.tiangolo.com/) für das moderne Web-Framework
- [Pydantic](https://pydantic-docs.helpmanual.io/) für Datenvalidierung
- [SQLAlchemy](https://www.sqlalchemy.org/) für ORM-Funktionalität

## 📞 Support

- **Dokumentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/unityai/n8n-playground/issues)
- **Discussions**: [GitHub Discussions](https://github.com/unityai/n8n-playground/discussions)
- **Email**: support@unityai.com

---

**Made with ❤️ by the UnityAI Team**

Modulare und erweiterbare n8n API Playground-Integration für das UnityAI-Projekt.

## 🏗️ Struktur

```
n8n-playground/
├── core/                           # Kern-Funktionalitäten
├── modules/                        # Feature-Module
├── config/                         # Konfiguration
├── templates/                      # Workflow Templates
├── tests/                          # Test Suite
└── docs/                          # Dokumentation
```

## 🚀 Quick Start

```bash
# Installation
cd n8n-playground
pip install -r requirements.txt

# Konfiguration
cp config/settings.example.py config/settings.py
# Bearbeite config/settings.py mit deinen n8n API Credentials

# Erste Tests
python -m pytest tests/unit/
```

## 📋 Module

### 1. Workflow-Automatisierung
- Python Script Execution
- Parameter Validation
- Result Processing

### 2. FastAPI Integration
- Bidirektionale API Calls
- Webhook Management
- Authentication

### 3. Monitoring
- Workflow Status Tracking
- Performance Metrics
- Health Checks

### 4. User Management
- User Registration
- Permission Management
- Notifications

## 📚 Dokumentation

Siehe [Integration Plan](../docs/n8n-api-playground-integration.md) für detaillierte Informationen.

## 🔧 Entwicklung

Jedes Modul enthält eine `SYSTEM_INSTRUCTIONS.md` Datei mit spezifischen Anweisungen und Workflows.