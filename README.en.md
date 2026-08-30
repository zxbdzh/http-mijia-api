<div align="center">

# Mijia HTTP API

[中文](README.md)

**Turn your Mijia smart-home devices into an HTTP API.** A REST server based on [mijia-api](https://github.com/Do1e/mijia-api): QR-code login, device & scene management, one-command Docker deploy.

<sub>// REST API · QR login · WebSocket status push · Web UI · Swagger docs</sub>

<br />

![Python](https://img.shields.io/badge/Python-FastAPI-3776ab?logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-compose-2496ed?logo=docker&logoColor=white)
![API Docs](https://img.shields.io/badge/docs-Swagger%20UI%20%2B%20ReDoc-85ea2d)
![License](https://img.shields.io/badge/License-MIT-green)

</div>

---

## Features

- 🌐 **HTTP REST API** — full device and scene management endpoints
- 🔐 **QR-code login** — authenticate with the Mi Home app
- 🔌 **WebSocket** — real-time login status push
- 📱 **Web UI** — a clean console for device and scene management
- 🐳 **Docker** — one-command deploy via Docker / Docker Compose
- 📖 **API docs** — Swagger UI and ReDoc generated automatically
- 🔒 **API key** — optional secret to protect service access

## Quick start

### Docker Compose (recommended)

```bash
git clone https://github.com/zxbdzh/http-mijia-api
cd http-mijia-api
docker-compose up -d
```

Open http://localhost:8000

### Run locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Web UI

1. **QR login** — click the button and scan with the Mi Home app
2. **Devices** — list devices, open details, control properties
3. **Scenes** — switch to the Scenes tab and run preset scenes

## API key protection

Set the `MIJIA_API_SECRET` environment variable to enable it, then append `?secret=your-key` to any URL (Web UI or API). Wrong or missing keys get an access-denied page.

## License

[MIT](./LICENSE)
