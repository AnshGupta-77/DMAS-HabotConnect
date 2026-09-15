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

## Documents

Visibility: admin sees all; creator sees own; reviewer sees all non-draft documents.

### `POST /api/documents/`
- Auth: required, role creator or admin (reviewer forbidden)
- Body (multipart): `title`, `description`, `category` (id), `file`
- 201: document; creates version 1, `document_created` activity
- 400: missing title/category/file, unsupported extension, spoofed content, oversized file

### `GET /api/documents/`
- Auth: required; paginated (`page_size`, max 100), role-scoped queryset
- Filters: `status` (exact choice, 400 on invalid), `category` (name, case-insensitive), `created_by` (id)
- `search=` matches title/category name/status/username; `ordering=` created_at/updated_at/title/status

### `GET /api/documents/{id}/`
- Auth: required; 404 if outside the caller's visible set

### `PATCH /api/documents/{id}/`
- Auth: required, owner or admin, only while `draft`/`changes_requested`
- `status`, `created_by`, `current_version` are read-only (ignored if sent)
- 403 if not owner/admin or status not editable

### `DELETE /api/documents/{id}/`
- Auth: required. Admin: any document. Creator: own drafts only.
- 204 on success; `document_deleted` activity recorded with `document=null`

### `GET /api/documents/{id}/download/`
- Auth: required, same object-access rules as retrieve
- 200: file stream (`FileResponse`), never a filesystem path in the JSON body
