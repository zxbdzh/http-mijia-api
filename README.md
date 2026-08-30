<div align="center">

# Mijia HTTP API

[English](README.en.md)

**把米家设备变成 HTTP API。** 基于 [mijia-api](https://github.com/Do1e/mijia-api) 的 REST 服务器，扫码登录、设备与场景管理、Docker 一键部署。

<sub>// REST API · 扫码登录 · WebSocket 状态推送 · Web UI · Swagger 文档</sub>

<br />

![Python](https://img.shields.io/badge/Python-FastAPI-3776ab?logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-compose-2496ed?logo=docker&logoColor=white)
![API Docs](https://img.shields.io/badge/docs-Swagger%20UI%20%2B%20ReDoc-85ea2d)
![License](https://img.shields.io/badge/License-MIT-green)

</div>

---

## 功能特性

- 🌐 **HTTP REST API** - 提供完整的设备和场景管理接口
- 🔐 **扫码登录** - 支持米家 App 扫码认证
- 🔌 **WebSocket** - 支持实时登录状态推送
- 📱 **Web UI** - 提供美观的 Web 控制台界面，支持设备和场景管理
- 🐳 **Docker 部署** - 支持 Docker 和 Docker Compose 一键部署
- 📖 **API 文档** - 提供 Swagger UI 和 ReDoc 自动生成文档
- 🔒 **API 密钥** - 支持配置 API 密钥保护服务访问

## 快速开始

### 方式一：Docker Compose（推荐）

```bash
# 克隆项目
git clone https://github.com/zxbdzh/http-mijia-api
cd http-mijia-api

# 启动服务
docker-compose up -d
```

访问 http://localhost:8000

### 方式二：本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 运行服务
uvicorn app.main:app --reload
```

## Web UI 使用

启动后访问 http://localhost:8000 ，您将看到米家 API 控制台：

1. **扫码登录** - 点击"扫码登录"按钮，使用米家 App 扫描二维码
2. **设备管理** - 查看设备列表，点击设备查看详情和控制属性
3. **场景执行** - 切换到"场景"标签，执行预设场景

## API 密钥保护

### 配置 API 密钥

设置环境变量 `MIJIA_API_SECRET` 来启用密钥保护：

```bash
# Linux/Mac
export MIJIA_API_SECRET=your-secret-key

# Windows CMD
set MIJIA_API_SECRET=your-secret-key

# Windows PowerShell
$env:MIJIA_API_SECRET="your-secret-key"
```

### Docker Compose 配置

在 `docker-compose.yml` 中添加环境变量：

```yaml
environment:
  - MIJIA_API_SECRET=your-secret-key
```

### 访问受保护的服务

配置密钥后，访问时需要在 URL 后添加 `?secret=你的密钥`：

- Web UI：http://localhost:8000/?secret=your-secret-key
- API：http://localhost:8000/api/v1/devices/?secret=your-secret-key

如果密钥错误或未提供，将显示访问被拒绝提示页面。

## API 使用指南

### 认证状态

```bash
# 检查认证状态（需要密钥）
curl http://localhost:8000/api/v1/auth/status?secret=your-secret-key

# 发起登录（获取二维码）
curl -X POST http://localhost:8000/api/v1/auth/login?secret=your-secret-key

# 取消登录
curl -X POST http://localhost:8000/api/v1/auth/login/cancel?secret=your-secret-key

# 退出登录
curl -X POST http://localhost:8000/api/v1/auth/logout?secret=your-secret-key
```

### 设备管理

```bash
# 获取设备列表（自动合并普通设备和共享设备，去重）
curl http://localhost:8000/api/v1/devices/?secret=your-secret-key

# 获取单个设备信息
curl http://localhost:8000/api/v1/devices/{did}?secret=your-secret-key

# 获取设备型号信息（属性列表、动作列表）
curl http://localhost:8000/api/v1/devices/{did}/info?secret=your-secret-key

# 获取设备属性
curl http://localhost:8000/api/v1/devices/{did}/properties?secret=your-secret-key

# 获取指定属性
curl http://localhost:8000/api/v1/devices/{did}/properties/power?secret=your-secret-key

# 设置属性（布尔值示例）
curl -X PUT "http://localhost:8000/api/v1/devices/{did}/properties/power?secret=your-secret-key" \
     -H "Content-Type: application/json" \
     -d 'true'

# 执行设备动作
curl -X POST http://localhost:8000/api/v1/devices/{did}/actions/start?secret=your-secret-key
```

### 场景管理

```bash
# 获取场景列表
curl http://localhost:8000/api/v1/scenes?secret=your-secret-key

# 执行场景
curl -X POST http://localhost:8000/api/v1/scenes/{scene_id}?secret=your-secret-key
```

## WebSocket 实时状态

登录时可以通过 WebSocket 实时接收登录状态：

```
ws://localhost:8000/api/v1/auth/ws/login
```

WebSocket 消息：

- `{"status": "waiting", "qr_image": "..."}` - 等待扫码
- `{"status": "success", "user_id": "..."}` - 登录成功
- `{"status": "error", "error": "..."}` - 登录失败

## API 文档

启动服务后访问：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 环境变量

| 变量名              | 默认值    | 说明                          |
| ------------------- | --------- | ----------------------------- |
| `MIJIA_HOST`        | `0.0.0.0` | 服务监听地址                   |
| `MIJIA_PORT`        | `8080`    | 服务监听端口                   |
| `MIJIA_DATA_DIR`    | `./data`  | 认证数据存储目录               |
| `MIJIA_LOG_LEVEL`   | `INFO`    | 日志级别                       |
| `MIJIA_DEBUG`       | `false`   | 是否启用调试模式               |
| `MIJIA_API_SECRET`  | (空)      | API 密钥，留空则不启用保护     |

## Docker 部署

### 使用 Docker

```bash
# 构建镜像
docker build -t http-mijia-api .

# 运行容器
docker run -d \
  --name mijia-api \
  -p 8080:8080 \
  -v mijia-data:/app/data \
  -e MIJIA_API_SECRET=your-secret-key \
  http-mijia-api
```

### 使用 Docker Compose

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

默认端口：8080

## 项目结构

```
http-mijia-api/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI 应用入口
│   ├── config.py         # 配置管理
│   ├── dependencies.py   # 认证依赖
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py       # 认证 API
│   │   ├── devices.py    # 设备 API
│   │   └── scenes.py     # 场景 API
│   ├── services/
│   │   ├── __init__.py
│   │   └── mijia.py      # 米家 API 封装（单实例模式）
│   └── templates/
│       └── index.html    # Web UI
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## 技术说明

### 单实例模式

本项目采用单实例模式：

- 所有请求共享同一个米家账号登录状态
- 认证数据持久化到 `data/auth.json`
- 无需 Session 管理，简化部署

### 设备列表合并

`GET /api/v1/devices/` 接口会：

1. 获取普通设备列表
2. 获取共享设备列表
3. 按设备 ID (did) 去重合并
4. 返回无重复的完整设备列表

### API 密钥认证

当配置 `MIJIA_API_SECRET` 环境变量后：

- 根路径 `/` 和所有 `/api/v1/*` 接口都需要验证
- 验证方式：在 URL 查询参数中添加 `?secret=你的密钥`
- 未提供或错误的密钥将返回访问被拒绝页面/错误信息
- WebSocket 连接不受密钥保护（由应用层控制）

## 注意事项

1. **二维码有效期**：二维码有效期约 2 分钟，需要在有效期内完成扫码
2. **数据持久化**：Docker 部署时建议挂载数据卷 `/app/data` 以保存登录状态
3. **安全性**：生产环境建议配合反向代理（如 Nginx）使用 HTTPS
4. **设备离线**：离线设备无法获取属性和执行动作
5. **API 密钥**：生产环境请务必设置 `MIJIA_API_SECRET` 防止未授权访问

## License

MIT License
