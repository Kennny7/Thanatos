# Thanatos Production Deployment & Security Hardening Guide

This document outlines the end-to-end procedure for deploying Thanatos to a remote server, Virtual Private Server (VPS), or dedicated hardware for private, secure personal use.

---

## 1. Network Topology & Ports

| Service | Container Port | Host Port | Protocol | Recommended Access | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Caddy Proxy** | 80, 443 | 80, 443 | HTTP / HTTPS / WSS | Public | Auto-TLS termination and reverse proxy |
| **FastAPI Gateway**| 8000 | (Internal) | HTTP / WS | Internal only | Core agent loop, REST API, WebSocket handler |
| **Ollama Engine** | 11434 | 11434 (Local)| HTTP | Localhost / Docker net | Local LLM inference server |
| **ChromaDB** | 8000 | 8001 | HTTP | Localhost / Docker net | Vector store for hybrid long-term memory |

> [!WARNING]
> Never expose ports `8000`, `11434`, or `8001` directly to the public internet without firewall restrictions. All public client traffic should flow through the encrypted Caddy reverse proxy on port `443` (`https://` and `wss://`).

---

## 2. Server Prerequisites

1. **Operating System**: Ubuntu 22.04 LTS or Debian 12 recommended.
2. **Hardware Specs**:
   - **Minimum**: 4 CPU Cores, 16 GB RAM (for running 7B/8B models on CPU).
   - **Recommended**: 8 CPU Cores, 32 GB RAM, NVIDIA GPU with 12GB+ VRAM (RTX 3060, 4070, or A10G/T4).
3. **Software**:
   - Docker Engine & Docker Compose (`docker compose version >= 2.20`).
   - NVIDIA Container Toolkit (if using GPU acceleration).

---

## 3. One-Command Production Deployment (Docker Compose)

### Step 1: Clone Repository
```bash
git clone https://github.com/Kennny7/Thanatos.git /opt/thanatos
cd /opt/thanatos
```

### Step 2: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Edit `.env`:
```env
ENVIRONMENT=production
PORT=8000
HOST=0.0.0.0

# LLM Configuration
LLM_PROVIDER=ollama
LLM_BASE_URL=http://ollama:11434
LLM_MODEL=qwen2.5:7b

# Security: Generate a strong random bearer token
API_AUTH_TOKEN=your_generated_random_secret_token_here
ALLOWED_ORIGINS=https://your-domain.com

# Memory Settings
MEMORY_PERSIST_DIR=/app/memory_store
MEMORY_COLLECTION=thanatos_memories
```

### Step 3: Domain & Auto-HTTPS Configuration
Edit `infra/docker/Caddyfile`:
```caddy
your-domain.com {
    reverse_proxy api-server:8000
}
```

### Step 4: Launch Stack
```bash
docker compose up -d --build
```
This automatically boots:
- Ollama runtime and provisions `qwen2.5:7b`
- ChromaDB vector store
- FastAPI application gateway with auth middleware
- Caddy reverse proxy with automatic SSL certificate provisioning

---

## 4. Connecting the Flutter Client to Production

In your Flutter client (`apps/client_flutter/assets/.env` or runtime settings):

1. Change `API_BASE_URL`:
   ```env
   API_BASE_URL=https://your-domain.com
   WEBSOCKET_URL=wss://your-domain.com/ws
   ```
2. Pass authentication token:
   The WebSocket URL automatically includes the auth query parameter:
   `wss://your-domain.com/ws?token=your_generated_random_secret_token_here`

---

## 5. Security Hardening Checklist

- [x] **Bearer Authentication**: Enabled via `API_AUTH_TOKEN` in `apps/api_server/middleware/auth.py`.
- [x] **Encrypted Transmissions**: All WebSocket and REST traffic encrypted using TLS 1.3 via Caddy.
- [x] **Firewall (UFW)**:
  ```bash
  sudo ufw default deny incoming
  sudo ufw default allow outgoing
  sudo ufw allow 22/tcp
  sudo ufw allow 80/tcp
  sudo ufw allow 443/tcp
  sudo ufw enable
  ```
- [x] **Merkle Audit Trail**: All autonomous operations are cryptographically hashed and logged to `./audit/storage/audit_log.json`.
- [x] **Tamper Protection**: Verify audit log integrity periodically using `services/audit/chain_manager.py`.

---

## 6. Systemd Native Service (Alternative to Docker)

If you prefer running natively on Ubuntu without Docker:

Create `/etc/systemd/system/thanatos.service`:
```ini
[Unit]
Description=Thanatos AI Assistant Gateway
After=network.target

[Service]
Type=simple
User=thanatos
WorkingDirectory=/opt/thanatos
ExecStart=/opt/thanatos/venv/bin/uvicorn apps.api_server.main:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always
RestartSec=5
EnvironmentFile=/opt/thanatos/.env

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable thanatos
sudo systemctl start thanatos
```
