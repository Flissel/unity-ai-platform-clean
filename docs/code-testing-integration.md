# Unity AI Code Testing Integration

## Überblick

Dieses System implementiert ein Multi-Agent Code-Testing-System mit AutoGen Core, das über n8n Workflows ausgeführt werden kann. Das System folgt einem **Coder → Tester → Reporter → Validator → Termination** Gesprächsmuster für robuste Code-Entwicklung und -Validierung.

## Architektur

### Agent-Team Struktur

1. **CoderAgent**: Generiert Code basierend auf Aufgabenbeschreibungen
2. **TesterAgent**: Führt Code in sicherer Sandbox-Umgebung aus (Docker/Subprocess)
3. **ReporterAgent**: Analysiert Testergebnisse und erstellt detaillierte Berichte
4. **ValidatorAgent**: Bewertet Code-Qualität und entscheidet über Iteration oder Abschluss

### Workflow-Pattern

```
CodeGenerationTask → CoderAgent → GeneratedCode
                                      ↓
TestingTask ← TesterAgent ← GeneratedCode
     ↓
TestResults → ReporterAgent → TestReport
                                   ↓
ValidationResult ← ValidatorAgent ← TestReport
     ↓
[Iteration oder Termination]
```

## Konfiguration

### Umgebungsvariablen

```env
# .env.fastapi
OPENAI_API_KEY=your_openai_api_key_here
AUTOGEN_API_KEY=not_used_but_present
REDIS_URL=redis://localhost:6379
N8N_API_URL=http://localhost:5678
N8N_API_KEY=your_n8n_api_key
```

### Docker-Konfiguration

Das System verwendet Docker für sichere Code-Ausführung:

- **Python**: `python:3.11-slim` Container
- **JavaScript**: `node:18-alpine` Container
- **Fallback**: Subprocess-Ausführung wenn Docker nicht verfügbar

## API-Endpunkte

### Haupt-Testing-Endpunkt

```http
POST /api/v1/code-testing/test
Content-Type: application/json

{
  "task_description": "Create a Python function that calculates factorial",
  "programming_language": "python",
  "requirements": ["Handle edge cases", "Include error handling"],
  "test_criteria": ["functionality", "syntax", "best_practices"],
  "user_id": "user123",
  "max_iterations": 3,
  "quality_threshold": 80
}
```

### Schnell-Test-Endpunkt

```http
POST /api/v1/code-testing/quick-test
Content-Type: application/json

{
  "code": "def factorial(n): return 1 if n <= 1 else n * factorial(n-1)",
  "programming_language": "python",
  "test_type": "execution"
}
```

### Status-Überwachung

```http
GET /api/v1/code-testing/status/{session_id}
GET /api/v1/code-testing/sessions
DELETE /api/v1/code-testing/sessions/{session_id}
```

### n8n Webhook Integration

```http
POST /api/v1/code-testing/n8n-webhook
Content-Type: application/json

{
  "task_description": "Create a sorting algorithm",
  "programming_language": "python",
  "webhook_callback_url": "https://your-n8n-instance.com/webhook/callback",
  "requirements": ["Efficient algorithm", "Handle empty arrays"]
}
```

## n8n Workflow Integration

### Workflow-Datei

Der vorgefertigte Workflow befindet sich in:
```
n8n/workflows/code-testing-workflow.json
```

### Workflow-Schritte

1. **Trigger**: Manual oder Webhook
2. **Prepare Request**: Eingabedaten formatieren
3. **Call Code Testing API**: Haupt-Testing-Prozess
4. **Check Success**: Erfolg/Fehler-Verzweigung
5. **Format Response**: Ergebnis formatieren
6. **Quick Validation**: Zusätzliche Validierung
7. **Send Callback**: Optional Callback senden

### Workflow Import

1. Öffne n8n Interface
2. Gehe zu "Workflows" → "Import from file"
3. Wähle `code-testing-workflow.json`
4. Konfiguriere FastAPI-URL (standardmäßig `http://fastapi:8000`)
5. Aktiviere den Workflow

## Verwendung

### 1. Über n8n Workflow

```json
{
  "task_description": "Create a function to validate email addresses",
  "programming_language": "python",
  "requirements": [
    "Use regex for validation",
    "Handle international domains",
    "Return boolean result"
  ],
  "test_criteria": ["functionality", "syntax", "best_practices"],
  "max_iterations": 3,
  "quality_threshold": 85
}
```

### 2. Direkte API-Aufrufe

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/code-testing/test",
    json={
        "task_description": "Create a binary search function",
        "programming_language": "python",
        "requirements": ["Handle sorted arrays", "Return index or -1"],
        "user_id": "developer123"
    }
)

result = response.json()
print(f"Session ID: {result['session_id']}")
print(f"Success: {result['success']}")
print(f"Final Code: {result['final_code']}")
```

### 3. Webhook Integration

```javascript
// n8n Webhook Node
const webhookData = {
  task_description: "Create a REST API endpoint",
  programming_language: "javascript",
  requirements: [
    "Use Express.js",
    "Include error handling",
    "Return JSON responses"
  ],
  webhook_callback_url: "https://your-app.com/webhook/code-result"
};

return [{ json: webhookData }];
```

## Antwort-Formate

### Erfolgreiche Antwort

```json
{
  "success": true,
  "session_id": "session_123456789",
  "final_code": "def factorial(n):\n    if n < 0:\n        raise ValueError('Negative numbers not allowed')\n    return 1 if n <= 1 else n * factorial(n-1)",
  "final_report": "Code successfully implements factorial calculation with proper error handling...",
  "total_iterations": 2,
  "execution_time": 45.2,
  "reason": "quality_threshold_met"
}
```

### Fehler-Antwort

```json
{
  "success": false,
  "session_id": "session_123456789",
  "final_report": "Failed to generate working code after 3 iterations. Last error: Syntax error in line 5...",
  "total_iterations": 3,
  "execution_time": 120.5,
  "reason": "max_iterations_reached"
}
```

## Sicherheit

### Sandbox-Ausführung

- **Docker-Container**: Isolierte Ausführungsumgebung
- **Zeitlimits**: Verhindert unendliche Schleifen
- **Ressourcen-Limits**: Begrenzte CPU/Memory-Nutzung
- **Netzwerk-Isolation**: Kein Internet-Zugang in Containern

### Code-Validierung

- **Syntax-Prüfung**: Vor Ausführung
- **Sicherheits-Scan**: Gefährliche Funktionen blockiert
- **Output-Limits**: Begrenzte Ausgabegröße

## Monitoring und Logging

### Metriken

- Session-Erfolgsrate
- Durchschnittliche Iterationen
- Ausführungszeiten
- Fehlertypen und -häufigkeit

### Logs

```
2024-01-15 10:30:15 [INFO] Starting code testing session: session_123456789
2024-01-15 10:30:16 [INFO] CoderAgent generated initial code (45 lines)
2024-01-15 10:30:18 [INFO] TesterAgent executed code successfully
2024-01-15 10:30:19 [INFO] ReporterAgent created test report (score: 85)
2024-01-15 10:30:20 [INFO] ValidatorAgent approved code (quality threshold met)
2024-01-15 10:30:20 [INFO] Session completed successfully
```

## Fehlerbehebung

### Häufige Probleme

1. **OpenAI API Key fehlt**
   ```
   Error: OpenAI API key not configured
   Lösung: OPENAI_API_KEY in .env.fastapi setzen
   ```

2. **Docker nicht verfügbar**
   ```
   Warning: Docker not available, using subprocess fallback
   Lösung: Docker installieren und starten
   ```

3. **n8n Webhook nicht erreichbar**
   ```
   Error: Failed to send webhook callback
   Lösung: n8n URL und API Key prüfen
   ```

### Debug-Modus

```python
# Aktiviere Debug-Logging
import logging
logging.getLogger("code_testing_agents").setLevel(logging.DEBUG)
```

## Erweiterungen

### Neue Programmiersprachen

1. Erweitere `TesterAgent.execute_code()` Methode
2. Füge entsprechende Docker-Images hinzu
3. Update `programming_language` Validierung

### Custom Test-Kriterien

1. Erweitere `TestCriteria` Enum
2. Update `ReporterAgent` Bewertungslogik
3. Anpassung der Prompts

### Integration mit anderen Tools

- **GitHub Actions**: Automatische Code-Reviews
- **Slack**: Benachrichtigungen über Test-Ergebnisse
- **Jira**: Ticket-Updates basierend auf Code-Qualität

## Performance-Optimierung

### Caching

- Code-Templates für häufige Aufgaben
- Vorkompilierte Docker-Images
- Redis-Cache für Zwischenergebnisse

### Parallelisierung

- Mehrere Test-Sessions gleichzeitig
- Asynchrone Agent-Kommunikation
- Load-Balancing für Docker-Container

## Lizenz und Support

Dieses System ist Teil der Unity AI Plattform. Für Support und Fragen:

- **Dokumentation**: `/docs/`
- **API-Referenz**: `http://localhost:8000/docs`
- **Health-Check**: `http://localhost:8000/health`