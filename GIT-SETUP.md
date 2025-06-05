# 🔧 Git Repository Setup - Unity AI

## ✅ Aktueller Status

```bash
✅ Lokales Git Repository initialisiert
✅ Initial Commit erstellt (03b5b29)
✅ Alle Projektdateien committed
✅ .gitignore konfiguriert (Secrets, Logs, etc.)
```

## 🚀 Nächste Schritte

### 1. Remote Repository erstellen

#### Option A: GitHub (Empfohlen)
```bash
# 1. Auf GitHub neues Repository erstellen: "unityai"
# 2. Remote hinzufügen
git remote add origin https://github.com/IHR-USERNAME/unityai.git

# 3. Push zum Remote
git branch -M main
git push -u origin main
```

#### Option B: GitLab
```bash
# 1. Auf GitLab neues Projekt erstellen
# 2. Remote hinzufügen
git remote add origin https://gitlab.com/IHR-USERNAME/unityai.git

# 3. Push zum Remote
git branch -M main
git push -u origin main
```

#### Option C: Eigener Git-Server
```bash
# Auf dem VPS (78.46.234.142)
ssh -i C:\Users\User\ssh-server root@78.46.234.142

# Bare Repository erstellen
git init --bare /opt/git/unityai.git
chown -R git:git /opt/git/unityai.git

# Lokal Remote hinzufügen
git remote add origin root@78.46.234.142:/opt/git/unityai.git
git push -u origin master
```

### 2. Deployment Workflow

#### Automatisches Deployment (Empfohlen)
```bash
# Post-receive Hook auf dem Server
cat > /opt/git/unityai.git/hooks/post-receive << 'EOF'
#!/bin/bash
cd /opt/unity/unityai
git --git-dir=/opt/git/unityai.git --work-tree=/opt/unity/unityai checkout -f

# Docker Stack neu starten
docker compose down
docker compose up -d

echo "✅ Unity AI deployed successfully!"
EOF

chmod +x /opt/git/unityai.git/hooks/post-receive
```

#### Manuelles Deployment
```bash
# Auf dem Server
cd /opt/unity/unityai
git pull origin main
docker compose down
docker compose up -d
```

### 3. Branching-Strategie

```
main/master     ← Produktions-Branch (Auto-Deploy)
├── develop     ← Development-Branch
├── feature/*   ← Feature-Branches
└── hotfix/*    ← Hotfix-Branches
```

#### Workflow
```bash
# Feature entwickeln
git checkout -b feature/neue-funktion
# ... Entwicklung ...
git add .
git commit -m "✨ Neue Funktion implementiert"
git push origin feature/neue-funktion

# Merge Request/Pull Request erstellen
# Nach Review: Merge in develop
# Nach Testing: Merge in main (Auto-Deploy)
```

### 4. Git-Konfiguration

```bash
# User-Konfiguration
git config user.name "Ihr Name"
git config user.email "ihre.email@unit-y.ai"

# Globale .gitignore
git config --global core.excludesfile ~/.gitignore_global

# Line-Ending-Handling (Windows)
git config --global core.autocrlf true
```

### 5. Useful Git Commands

```bash
# Status & Logs
git status
git log --oneline --graph
git show HEAD

# Branching
git branch -a
git checkout -b new-branch
git merge feature-branch

# Remote Management
git remote -v
git fetch origin
git pull origin main

# Rollback (Notfall)
git reset --hard HEAD~1
git revert <commit-hash>
```

## 🔒 Security Best Practices

### SSH-Keys für Git
```bash
# SSH-Key generieren
ssh-keygen -t ed25519 -C "git@unit-y.ai"

# Public Key zu GitHub/GitLab hinzufügen
cat ~/.ssh/id_ed25519.pub

# SSH-Agent konfigurieren
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# SSH-URL verwenden
git remote set-url origin git@github.com:IHR-USERNAME/unityai.git
```

### Secrets Management
```bash
# NIEMALS committen:
*.key, *.pem, *password*, *secret*, *token*

# Git-Secrets installieren (optional)
git secrets --install
git secrets --register-aws
```

## 📊 Repository-Statistiken

```bash
# Aktueller Stand
Dateien: 22
Commits: 1
Branches: 1 (master)
Remotes: 0 (noch nicht konfiguriert)

# Größe
Repository: ~50KB
Working Tree: ~45KB
```

## 🚨 Troubleshooting

### Häufige Probleme

**Remote bereits existiert:**
```bash
git remote remove origin
git remote add origin <neue-url>
```

**Line-Ending-Probleme:**
```bash
git config core.autocrlf true
git rm --cached -r .
git reset --hard
```

**Merge-Konflikte:**
```bash
git status
# Konflikte manuell lösen
git add .
git commit
```

---

**Nächster Schritt**: Remote Repository erstellen und `git push` ausführen!