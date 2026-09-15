# DMAS API Reference

Base path: `/api/`. All protected endpoints require `Authorization: Bearer <access token>`.

## Authentication

### `POST /api/auth/register/`
- Auth: none
- Body: `username`, `email`, `password`, `role` (`creator` | `reviewer` — `admin` is rejected; use `createsuperuser`)
- 201: `{id, username, email, role}`
- 400: validation errors (duplicate username/email, weak password, invalid role)

### `POST /api/auth/login/`
- Auth: none
- Body: `username`, `password`
- 200: `{access, refresh}`
- 401: bad credentials

### `POST /api/auth/login/refresh/`
- Auth: none
- Body: `refresh`
- 200: `{access, refresh}` (rotated, old refresh blacklisted)
- 401: invalid/blacklisted token

### `POST /api/auth/logout/`
- Auth: required
- Body: `refresh`
- 205: refresh token blacklisted
- 400: missing/invalid refresh token

### `GET /api/auth/profile/`
- Auth: required
- 200: `{id, username, email, role}`
