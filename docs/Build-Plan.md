# DMAS Build Plan — Document Management & Approval System

## Context
`DMAS/docs/Product-Brief.md` (SRS) + `DMAS/docs/rules.md` (engineering rules) define an assessment project: a **Django + DRF backend** for uploading documents, running them through a review/approval state machine, with comments, versions, audit log, in-app notifications, dashboard API. No code exists yet; `DMAS/` is not a git repo. Goal: build the full brief scope, following every rule (security first, no dead code, tests per feature, docs updated per feature, one short git commit per phase).

Environment verified: Python 3.14.5, PostgreSQL 16 running locally (Homebrew, port 5432), git 2.54.

## User decisions (confirmed)
- **Dashboard = API only** (`GET /api/dashboard/` JSON). No HTML frontend. Chrome testing via DRF browsable API + Django admin.
- **Auth = JWT** via `djangorestframework-simplejwt`; logout blacklists refresh token (`token_blacklist` app, ships with same package).
- **Roles**: keep exactly three (admin, creator, reviewer). Admin never self-assignable. No invented features. Implementation: register accepts `role` limited to `creator|reviewer` (brief needs both to register for E2E flow step 1); admin only via `createsuperuser`.
- **Repo root = `DMAS/`**. Remote: `https://github.com/AnshGupta-77/DMAS-HabotConnect` (verified empty). Branch `main`; `git remote add origin ...` in Phase 0.
- Commits: short conventional messages (`feat: add jwt auth`), one per phase after tests pass, then `git push origin main` (first push `-u`).

## Interpretation decisions (documented in README "Design decisions", per rules 2.1)
1. **Reviewer visibility** ("assigned/available"): no assignment model in brief → reviewers see all non-Draft documents. Creator sees own. Admin sees all.
2. **Categories**: `Category` model (FK), seeded HR/Finance/Technical/Legal/General via data migration; admin manages via Django admin (brief lists no category API). "View all users" / "view audit records" for admin also via Django admin + activity API.
3. **Status transitions** only through workflow endpoints; `status`, `created_by`, `current_version` read-only in serializers.
4. **Changes Requested → Draft**: happens automatically when owner edits (PATCH) or uploads a new version on a `changes_requested` doc (no extra endpoint exists in brief).
5. **Editing**: PATCH (title/description/category) allowed for owner/admin only in `draft`/`changes_requested`. File changes go only through `POST versions/` so history stays consistent. Approved docs never overwritten.
6. **Versions**: v1 auto-created on document create. `POST versions/` (owner/admin) allowed in `draft`, `changes_requested`, `approved`, `rejected`; blocked while `submitted`/`under_review`. Creates version N+1, updates `document.file` + `current_version`, sets status `draft` (must go through review again). Old version records + files retained.
7. **Rejection reason / change-request comment** stored as `Comment` rows + activity description (no extra fields).
8. **Delete**: admin any, creator own drafts. `ActivityLog.document` uses `SET_NULL` so "Document Deleted" entry survives; description holds id + title. Stored files removed on delete.
9. **Secure file download (flagged scope addition, security-required)**: media NOT served publicly (rule 9.2 "unauthorized file retrieval"). Add `GET /api/documents/{id}/download/` and `GET /api/documents/{id}/versions/{version_id}/download/`, object-permission checked, `FileResponse`. Responses expose download URL, never filesystem path.
10. **Dashboard scope**: counts over the caller's visible queryset. `submitted_documents`=submitted, `pending_reviews`=under_review.
11. **Notifications**: submit → all active reviewers ("You have a document waiting for review."); approve/reject/request-changes → creator.
12. Browsable API usable in Chrome: `SessionAuthentication` enabled **only when DEBUG** (CSRF enforced), JWT always.

## Tech & dependencies (each justified)
`requirements.txt`: Django 5.2 LTS (or 6.0 if 5.2 lacks 3.14 support — check at install), djangorestframework, djangorestframework-simplejwt, django-filter (validated filter params → 400 on bad enum), psycopg[binary] (Postgres).
`requirements-dev.txt`: ruff (unused imports/dead code lint). Tests: Django `APITestCase` (no pytest dep).
Config: plain `os.environ`; `.env.example` committed, `.env` gitignored. `DJANGO_SECRET_KEY`, DB vars required — app fails loudly if missing when `DEBUG=False`. `MAX_UPLOAD_SIZE_MB` (default 10).

## Project structure (`DMAS/`)
```
manage.py  requirements.txt  requirements-dev.txt  ruff.toml  .gitignore  .env.example  README.md
config/    settings.py urls.py exceptions.py (custom handler → {"error": "...", "details": {...}}) pagination.py
users/     models.py (User w/ role) serializers.py views.py urls.py permissions.py admin.py tests/
documents/ models.py (Category, Document, DocumentVersion, Comment, ActivityLog) serializers.py views.py urls.py
           permissions.py filters.py services.py (workflow, versions, activity) validators.py (file checks) admin.py tests/
notifications/ models.py serializers.py views.py urls.py services.py admin.py tests/
dashboard/ views.py urls.py tests/
docs/      Product-Brief.md rules.md API.md endpoint-matrix.md DMAS.postman_collection.json
```

## Models
- `User(AbstractUser)`: `role` choices admin/creator/reviewer (CheckConstraint); `create_superuser` sets admin.
- `Category`: name unique.
- `Document`: title, description, category FK(PROTECT), file (upload_to → `documents/<uuid>.<ext>`, original name discarded), created_by FK(PROTECT), status TextChoices + CheckConstraint, current_version PositiveInt, created_at, updated_at. Indexes: `(created_by, status)`, `status`, `-created_at`.
- `DocumentVersion`: document FK(CASCADE), version_number, file, created_by, comment, created_at. `UniqueConstraint(document, version_number)`.
- `Comment`: document, user, comment (non-blank), created_at.
- `ActivityLog`: document FK(SET_NULL, null), user FK(SET_NULL), action TextChoices, description, created_at; index `(document, -created_at)`.
- `Notification`: user FK(CASCADE), message, is_read, created_at; index `(user, is_read)`.

## Cross-cutting rules applied every phase
- **Permissions**: DRF permission classes (`IsAdmin`, `IsCreator`, `IsReviewerOrAdmin`, `DocumentObjectPermission`); querysets pre-scoped by role so ID manipulation returns 404.
- **Transactions/concurrency**: every workflow/version service runs in `transaction.atomic()` with `select_for_update()` on the document row; status check happens after lock; activity + notification + comment written in same transaction. Version number = locked `current_version + 1` + unique constraint.
- **File validation** (`validators.py`, stdlib only): required, extension whitelist (pdf/doc/docx/xls/xlsx/txt), size ≤ limit, magic-byte check (`%PDF-`; OLE2 `D0CF11E0` for doc/xls; zip with `word/` or `xl/` entry for docx/xlsx; txt = valid UTF-8, no null bytes).
- **Performance**: `select_related('category','created_by')` on lists, `assertNumQueries` tests on list/detail/dashboard/activity/notifications, pagination (page_size 10, `page_size` param, max 100), dashboard single `aggregate(Count(filter=Q))`.
- **Errors**: custom exception handler, consistent JSON; no stack traces (DEBUG off in prod).
- **Tests per phase** cover: no auth / invalid token (401), wrong role (403), other user's object (404), invalid/whitespace/unexpected input (400), illegal transitions, unsupported methods (405).
- **Per-phase close-out** (rules 31.3/39): `python manage.py test` all green → `ruff check .` clean → `makemigrations --check` → review `git status`/`git diff` → update README / `docs/API.md` / `docs/endpoint-matrix.md` / Postman collection → commit.

## Phases (one commit each)

**Phase 0 — Scaffold** · `chore: scaffold django project`
git init in `DMAS/`, venv (`.venv`, ignored), install deps, `createdb dmas`, `config/` settings from env, DRF defaults (JWT auth, IsAuthenticated default, pagination, filter backends, exception handler), `.gitignore` (.venv, .env, media/, __pycache__, staticfiles), `.env.example`, `ruff.toml`, README skeleton (setup, env vars). Verify `runserver` + `check --deploy` sanity.

**Phase 1 — Users & auth** · `feat: add jwt auth and roles`
Custom User + migration, `register/` (role creator|reviewer, password validators, unique username/email), `login/` (simplejwt obtain pair), `logout/` (blacklist refresh), `profile/` (GET self), role permission classes, admin registration. Tests: register ok/duplicate/admin-role rejected/missing fields, login ok/bad creds, logout invalidates refresh, profile 401 without/with bad token.

**Phase 2 — Documents CRUD + upload** · `feat: add document upload and crud`
Category (+ seed migration), Document, DocumentVersion (v1 on create), ActivityLog model + `services.log_activity`, validators, serializers (read-only protected fields, download URL), viewset create/list/retrieve/partial_update/destroy (no PUT), download endpoints, role-scoped querysets, created/updated/deleted activity. Tests: create ok + draft + v1 + activity; reviewer cannot upload; missing title/category/file; bad extension; spoofed extension (exe renamed .pdf); oversized; retrieve own vs other creator (404); PATCH status ignored/rejected; edit approved blocked; delete own draft ok, non-draft blocked, admin delete; download authz.

**Phase 3 — Search, filter, pagination** · `feat: add document search and filters`
`filters.py` FilterSet: `status` (choice, case-insensitive values), `category` (name iexact), `created_by` (int); SearchFilter on title/category name/status/username; ordering. Tests: each filter, invalid status → 400, page_size cap, response keys count/next/previous/results, query count constant.

**Phase 4 — Notifications** · `feat: add in-app notifications`
Model, `services.notify(users, message)` via `bulk_create`, `GET /api/notifications/` (own, paginated, newest first), `PATCH /api/notifications/{id}/read/` (own only → other's id = 404). Tests incl. IDOR.

**Phase 5 — Workflow** · `feat: add review workflow`
`services.py` transition table `{action: (allowed_from, to)}` single source of truth; actions submit (owner/admin, draft→submitted, notify reviewers), review (reviewer/admin, submitted→under_review), approve / reject (reason required, non-whitespace → Comment) / request-changes (comment required → Comment), each logs activity + notifies creator, all atomic + locked. Tests: happy path each, creator approve/reject/review → 403, draft→approve 400, approved→approve 400, rejected→approve 400, empty/whitespace reason 400, notifications + activity created, reviewer cannot submit, other creator cannot submit.

**Phase 6 — Comments & activity API** · `feat: add comments and activity log api`
`GET/POST /api/documents/{id}/comments/` (any role with document access; user from request, never payload), `GET /api/documents/{id}/activity/` (paginated, `select_related('user')`). Tests: empty/whitespace 400, inaccessible doc 404, impersonation field ignored, activity entries ordered.

**Phase 7 — Versions** · `feat: add document versioning`
`POST/GET /api/documents/{id}/versions/`, `GET .../versions/{version_id}/` (scoped to parent doc → wrong doc 404), rules from decision 6, `changes_requested → draft`, activity "Version Created". Tests: number increments, approved doc → new version keeps old file record + status draft, blocked while under review, non-owner 403/404, version from other doc 404, invalid file.

**Phase 8 — Dashboard** · `feat: add dashboard api`
Single aggregate query over role-scoped queryset. Tests: counts per role, 401 unauthenticated, `assertNumQueries`.

**Phase 9 — E2E verification, audits, final docs** · `docs: finalize api docs` (+ `fix:` commits for anything found)
- Automated E2E test replicating brief §26 13-step flow (success + unauthorized branches).
- Manual E2E: `runserver`, curl script in scratchpad (not committed) through all 13 steps.
- **Claude in Chrome**: log into Django admin (categories, users, activity, notifications) and DRF browsable API (session, DEBUG) — list/filter/paginate documents, workflow actions, verify 403 for wrong role.
- Security audit (rule 41), performance audit (rule 42: query counts per endpoint), code quality audit (rule 43: ruff, no prints/TODOs), git audit (rule 44: clean tree, `git log --oneline`).
- Final: README (setup, env, architecture, models, design decisions, testing), `docs/API.md` (every endpoint: method, path, auth, roles, request, response, errors, workflow limits), `docs/endpoint-matrix.md` (rule 28 columns filled), Postman collection.

## Verification (every phase + final)
```
cd DMAS && source .venv/bin/activate
python manage.py makemigrations --check --dry-run
python manage.py test
ruff check .
git status && git diff --staged
git commit -m "<short msg>" && git push origin main
```
Target ≥ 25 meaningful tests total (brief asks 15–25; rules call it baseline). Final: full suite green, E2E flow verified via test + curl + Chrome, working tree clean.
