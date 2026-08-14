# 004 暴露面收紧 + OAuth state + API key 验证 SSRF（发现 #5、#6、#7）

## Status
- **Priority**: P1 · **Effort**: S · **Risk**: LOW · **Depends on**: none · **Category**: security
- **Planned at**: commit 1c03e8b, 2026-08-14

## Context
`.env` 为 `HOST=0.0.0.0`、`DEBUG=true`（异常详情回传客户端），各启动路径绑定不一致；OAuth 登录缺 `state`（login CSRF）；`/apikeys` 验证接口把用户可控 `base_url` 直接作为服务端 POST 目标（SSRF 探测内网）。

## Current state
- `backend/app/config.py:28-30` — `host="0.0.0.0"`, `debug=True`
- `backend/app/main.py:119-127` — debug 下异常消息/路径回传客户端；`main.py:156` `reload=settings.debug`
- `backend/app/api/router.py:43-51` 授权 URL 无 state；`53-97` callback 不校验 state
- `backend/app/api/apikeys.py:139-182` — `_preset_base_url(provider, base_url)` 用户 base_url 自由传入并 `httpx.post`
- `backend/.env` — HOST=0.0.0.0、DEBUG=true（用户已选「全部收紧」，需同步改）

## Spec
1. config 默认 `host="127.0.0.1"`、`debug=False`；`backend/.env` 同步 `HOST=127.0.0.1`、`DEBUG=false`
2. `main.py` 生产校验：`debug=False` 且 `jwt_secret=="set-in-env-file"` 已存在 → 保留；`__main__` 的 `reload=settings.debug` 删除（对齐 RULES「uvicorn 不带 --reload」）
3. OAuth：`/auth/login` 生成 `state=secrets.token_urlsafe(16)` 存入签名 HttpOnly cookie（`SameSite=Lax`），`/auth/callback` 校验 state 后清除 cookie
4. SSRF：`base_url` 仅允许 `PROVIDER_PRESETS` 白名单主机（hostname 精确匹配），自定义 base_url 仅限 https + 非私网网段校验；错误信息不再回显上游响应体
5. `README.md`/`.env.example` 注释同步默认绑定说明

## Verification
- [ ] 无 state 的 callback → 400；伪造 state → 400
- [ ] `base_url=http://127.0.0.1:6379` → 400（私网拒绝）
- [ ] debug=false 下触发 500 → 响应不含异常类型
- [ ] `python -c "from app.config import get_settings; s=get_settings(); assert s.host=='127.0.0.1'"`
