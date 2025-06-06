# Replace:
 FROM docker.n8n.io/n8nio/n8n:latest
   

# Als root für Package-Installation
USER root

# Python und Build-Dependencies installieren
RUN apk add --no-cache \
    python3 \
    py3-pip \
    g++ \
    python3-dev \
    && ln -sf python3 /usr/bin/python

# Python ML-Libraries installieren
RUN pip3 install --no-cache-dir \
    pandas==2.1.4 \
    numpy==1.24.4 \
    scikit-learn==1.3.2 \
    pdf-lib \
    puppeteer

# Zusätzliche nützliche Libraries für Automation
RUN pip3 install --no-cache-dir \
    requests==2.31.0 \
    beautifulsoup4==4.12.2 \
    openpyxl==3.1.2 \
    python-dateutil==2.8.2

# Zurück zu n8n User für Sicherheit
USER node

# Gesundheitscheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:5678/healthz || exit 1

# Standard n8n Entrypoint beibehalten
ENTRYPOINT ["tini", "--", "/docker-entrypoint.sh"]
