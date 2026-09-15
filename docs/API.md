# DMAS API Reference

Base path: `/api/`. All protected endpoints require `Authorization: Bearer <access token>`.

## Authentication

### `POST /api/auth/register/`
- Auth: none
- Body: `username`, `email`, `password`, `role` (`creator` | `reviewer` — `admin` is rejected; use `createsuperuser`)
- 201: `{id, username, email, role}`
- 400: validation errors (duplicate username, weak password, invalid role). Username is the account identity; email is not required to be unique.

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
- Editing a `changes_requested` document returns it to `draft`, so it can be resubmitted
- `file` is ignored here; replace files through `POST versions/`
- 403 if not owner/admin or status not editable

### `DELETE /api/documents/{id}/`
- Auth: required. Admin: any document. Creator: own drafts only.
- 204 on success; `document_deleted` activity recorded with `document=null`
- Stored document and version files are deleted only after the database delete commits

### `GET /api/documents/{id}/download/`
- Auth: required, same object-access rules as retrieve
- 200: file stream (`FileResponse`), never a filesystem path in the JSON body

## Notifications

### `GET /api/notifications/`
- Auth: required; own notifications only, paginated, newest first

### `PATCH /api/notifications/{id}/read/`
- Auth: required, own notification only
- 200: marks read; 404 if the notification belongs to another user (no ID leak)

## Workflow

State machine: `draft → submitted → under_review → approved`, with
`under_review → rejected` and `under_review → changes_requested → draft`
(the last hop happens automatically on the next edit/version, decision 4).

### `POST /api/documents/{id}/submit/`
- Auth: owner (creator) or admin; only from `draft`
- Notifies all active reviewers

### `POST /api/documents/{id}/review/`
- Auth: reviewer or admin; only from `submitted`

### `POST /api/documents/{id}/approve/`
- Auth: reviewer or admin (never the creator, even the document's own creator); only from `under_review`
- Notifies the creator

### `POST /api/documents/{id}/reject/`
- Auth: reviewer or admin; only from `under_review`
- Body: `reason` (required, non-blank) — stored as a `Comment`
- Notifies the creator

### `POST /api/documents/{id}/request-changes/`
- Auth: reviewer or admin; only from `under_review`
- Body: `comment` (required, non-blank) — stored as a `Comment`
- Notifies the creator

All five endpoints: 400 on illegal transition or missing/non-string reason/comment,
403 on wrong role, 404 if the document is outside the caller's visible
queryset. Each runs inside `transaction.atomic()` with
`select_for_update()` on the document row.

## Comments

### `POST /api/documents/{id}/comments/`
- Auth: required, same object-access rules as the document
- Body: `comment` (required, non-blank); `user` is always the requester, never the payload
- 400 empty/whitespace, 404 if the document is outside the caller's visible set

### `GET /api/documents/{id}/comments/`
- Auth: required, same object-access rules; paginated

## Activity

### `GET /api/documents/{id}/activity/`
- Auth: required, same object-access rules; paginated, newest first

## Versions

### `POST /api/documents/{id}/versions/`
- Auth: owner (creator) or admin
- Body (multipart): `file` (required), `comment` (optional)
- Allowed while `draft`/`changes_requested`/`approved`/`rejected`; 400 while `submitted`/`under_review`
- Creates version N+1, updates `document.file`/`current_version`, sets status back to `draft`
- Old version file records are kept, never overwritten

### `GET /api/documents/{id}/versions/`
- Auth: same as document access; paginated

### `GET /api/documents/{id}/versions/{version_id}/`
- Auth: same as document access; 404 if the version does not belong to `{id}` or `version_id` is not numeric

### `GET /api/documents/{id}/versions/{version_id}/download/`
- Auth: same as document access; `FileResponse`, no filesystem path in the JSON body

## Dashboard

### `GET /api/dashboard/`
- Auth: required. Counts computed over the caller's visible queryset (decision 10):
  admin = all documents, creator = own documents, reviewer = non-draft documents.
- 200: `{total_documents, draft_documents, submitted_documents, pending_reviews, approved_documents, rejected_documents}`
- Single `aggregate(Count(filter=Q(...)))` query (2 queries total incl. auth lookup)
