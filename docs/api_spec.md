# API Spec (M1)

## Auth APIs

### POST `/api/v1/auth/register`

- **说明**：注册新账号（仅支持允许域名）。
- **请求体**：
  - `email`：符合 RFC 的邮箱字符串（`EmailStr`），域名须在允许列表中（当前为 `a.com`、`b.com`）
  - `password`：字符串，遵循 M1 密码策略
- **成功响应**：`201 Created`
- **失败响应**：
  - `400 Bad Request`：域名不允许、密码策略不满足等；**若邮箱在本域已注册**，仅返回 `Unable to complete registration`（不暴露「已存在」字样，降低枚举风险）
  - `422 Unprocessable Entity`：邮箱格式非法等校验错误

### POST `/api/v1/auth/login`

- **说明**：账号登录并签发 JWT token。
- **请求体**：
  - `email`：`EmailStr`
  - `password`：字符串
- **成功响应**：`200 OK`
  - 返回：`access_token`、`token_type`（`bearer`）
- **失败响应**：
  - `401 Unauthorized`：账号或密码不匹配（不区分具体原因）
  - `423 Locked`：账号因连续登录失败被临时锁定（见下文「登录失败锁定」）

## Login Lockout (M1)

- **计数规则**：同一账号连续密码错误达到 `5` 次后触发锁定
- **锁定时长**：`15` 分钟（自触发时刻起）
- **锁定期间**：再次调用登录接口返回 `423 Locked`，即使密码正确也需等待解锁
- **解锁后**：失败计数清零；若登录成功，也会清零失败计数并清除锁定时间

## Password Policy

### M1 Baseline Policy (Current)

- 长度：`8-64` 个字符
- 必须包含至少 1 个字母（`a-z` 或 `A-Z`）
- 必须包含至少 1 个数字（`0-9`）
- 允许使用特殊字符
- 服务端只保存密码哈希，不保存明文密码

### Future Upgrade Policy (Planned)

- 至少包含：1 个大写字母 + 1 个小写字母 + 1 个数字 + 1 个特殊字符
- 可扩展弱口令黑名单校验（如常见弱密码）

### GET `/api/v1/auth/token-context`（仅 `APP_ENV=development`）

- **说明**：校验 Bearer JWT，返回令牌中的 `email` 与 `domain`（M1 隔离探针）。**`APP_ENV=production` 时不注册此路由**，对该 URL 的请求为**统一 404**（不进行 Bearer 校验，避免令牌探测）。
- **请求头**：
  - `Authorization: Bearer <access_token>`（必填）
  - `X-Intended-Domain`（可选）：若填写，必须与令牌中的 `domain` 一致，否则 **403** `Cross-domain request denied`
- **成功响应**：`200 OK`， body：`email`、`domain`

## JWT Payload (M1)

- `sub`：邮箱（全小写，与注册一致）
- `domain`：邮箱域名，须与 `sub` 解析结果一致
- `exp`：过期时间

## Domain Isolation

- 用户注册和登录按邮箱域名路由到对应域数据库
- 当前域映射：
  - `a.com` -> `data/domain_a/db/mail.db`
  - `b.com` -> `data/domain_b/db/mail.db`
- 非允许域名直接拒绝
- 存储层推荐入口：`get_session_for_token_domain(domain)`（对允许域名与映射做二次校验）
- 详见 `docs/architecture.md`
