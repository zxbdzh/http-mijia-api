# Mijia HTTP API

An HTTP API server based on [mijia-api](https://github.com/Do1e/mijia-api), with Docker deployment support. Control your Xiaomi/Mijia smart-home devices through a REST API.

[中文](README.md)

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
