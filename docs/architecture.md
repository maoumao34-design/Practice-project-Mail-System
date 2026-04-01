# 架构与双域隔离（M1）

## 进程与职责

- **Server**：账户、邮件存储、分发、附件、权限；对外 **RESTful API**。
- **Client（后续）**：仅通过 HTTP 调用 Server；**禁止**直连各域 SQLite 文件或附件目录。
- **Streamlit（展示）**：仅作为 API 消费者，不写业务规则。

## 双域物理隔离

- 两个允许域名：`a.com`、`b.com`。
- 数据目录一一对应、互不共享：
  - `a.com` → `data/domain_a/db/mail.db`、附件目录 `data/domain_a/attachments/`
  - `b.com` → `data/domain_b/db/mail.db`、附件目录 `data/domain_b/attachments/`
- 用户「邮箱 + 域名」在**本域库内唯一**；跨域库之间不存在共享读路径。

## 访问层与双重校验

1. **接口层**
   - 注册/登录：按请求体邮箱解析域名，在允许列表内则路由到对应库。
   - 带 JWT 的请求：`sub` 为邮箱，`domain` 为域；解码时校验 `domain` 与邮箱解析域一致。
   - 可选头 `X-Intended-Domain`：若与令牌域不一致 → **403**，错误信息 `Cross-domain request denied`（用于联调/测试跨域拒绝）。

2. **存储层**
   - 业务代码应使用 `get_session_for_token_domain(domain)` 打开会话，内部再次校验允许域名与存储映射。
   - 禁止用客户端随意传入的域字符串绕过 JWT（未来邮件 API 仅从 `get_auth_context` 取域）。

## JWT 约定（M1）

- 使用 **PyJWT** 签发/校验 HS256，避免依赖维护停滞且历史 CVE 较多的 jose 栈。
- 载荷字段：`sub`（email）、`domain`（与 `sub` 一致）、`exp`。
- 旧版仅含 `sub` 的令牌将无法通过校验，需重新登录。

## 启动自检（M1）

- **`APP_ENV=production`** 时若 `SECRET_KEY` 为空或为占位默认值，进程在 lifespan 中**拒绝启动**。
- **`allowed_domains`** 与 **`DOMAIN_STORAGE_MAP`** 的键集合必须完全一致，否则拒绝启动（防止只改环境变量漏改映射）。

## 错误码约定（与隔离相关）

- **403 Forbidden**：显式跨域意图被拒绝（如 `X-Intended-Domain` 不匹配）。
- **401 Unauthorized**：令牌无效、过期或载荷异常。

## 环境与调试接口

- 配置项 `app_env`（环境变量 **`APP_ENV`**）：`development` | `production`。
- `GET /api/v1/auth/token-context` **仅在 `development` 下注册路由**。**`production`** 下该路径**不存在**，任意请求（含任意 `Authorization`）均由框架返回**统一 404**，**不会**先校验 JWT，从而避免「无效令牌 401 / 有效令牌 404」的探测面。
- 生产环境双域隔离仍由 **JWT 域声明、`get_session_for_token_domain`、各域独立库** 保证，不依赖上述探针接口。
- **部署注意**：须在**进程启动、首次 import 应用代码之前**设置好 `APP_ENV=production`，否则已加载的开发态路由不会自动卸掉（需重启进程）。

## 后续扩展

- 邮件、草稿、附件等接口均挂依赖 `get_auth_context`，会话一律来自 `get_session_for_token_domain(auth["domain"])`。
