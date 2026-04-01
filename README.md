# mail_system — Dual-Domain Mail System（双域隔离邮件系统）

基于 Python 的双域隔离邮件系统练习项目。当前已完成 M1 的账号注册与登录（RESTful API）。

## Current Progress（当前进度）

- M1：注册/登录（进行中，已完成后端接口最小闭环）
- M2：收件箱/发件箱/草稿箱（未开始）
- M3：快捷回复/附件（未开始）
- M4：邮件撤回/测试完善（未开始）

## Tech Stack（技术栈）

- Server: FastAPI + Uvicorn
- Data: SQLite（双域物理隔离）
- ORM: SQLModel
- Auth: JWT（**PyJWT**，HS256）+ bcrypt（passlib）
- Client: CLI（开发）/Streamlit（展示）

## Environment & Security（环境与安全）

- 本地开发：保持 `APP_ENV=development`（默认），可使用 `GET /api/v1/auth/token-context` 做隔离联调。
- 生产部署：务必在**启动进程前**设置 **`APP_ENV=production`** 与**强随机** **`SECRET_KEY`**（不得为占位默认值，否则应用**拒绝启动**）；**不注册** `token-context` 路由；对该 URL 的请求为**统一 404**。
- 生产请使用 **HTTPS**，并控制 token 有效期与客户端存 token 方式。

## Quick Start（快速启动）

1. 创建并激活虚拟环境（Windows PowerShell）
   - `python -m venv .venv`
   - `.venv\Scripts\Activate.ps1`
2. 安装依赖
   - `pip install -r requirements.txt`
3. 可选：复制环境变量模板
   - `Copy-Item .env.example .env`
4. 启动服务
   - `python scripts/run_server.py`
5. 访问健康检查
   - `http://127.0.0.1:8000/health`

## REST API - M1（已有接口 · M1）

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/token-context`（需 Bearer；可选 `X-Intended-Domain` 做跨域拒绝演示）

## Data Isolation（数据隔离说明）

- 域名 `a.com` 使用 `data/domain_a/db/mail.db`
- 域名 `b.com` 使用 `data/domain_b/db/mail.db`
- 客户端禁止直连数据库，必须通过 API 访问服务端
