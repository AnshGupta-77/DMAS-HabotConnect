# DMAS — Document Management & Approval System

Django + DRF backend for uploading documents and routing them through a
review/approval workflow, with comments, versions, activity log, in-app
notifications and a dashboard API.

## Stack

Python 3.14, Django 6.1, Django REST Framework, PostgreSQL, JWT auth
(`djangorestframework-simplejwt`), `django-filter`.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # edit values for your machine

createdb dmas
python manage.py migrate
python manage.py createsuperuser   # admin role
python manage.py runserver
```

## Environment variables

| Variable | Purpose | Required |
|---|---|---|
| `DJANGO_SECRET_KEY` | Django secret key | yes in production (dev falls back to an insecure default) |
| `DEBUG` | `True`/`False` | no (default `False`) |
| `ALLOWED_HOSTS` | comma-separated hosts | in production |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | PostgreSQL connection | yes |
| `MAX_UPLOAD_SIZE_MB` | max upload size, default 10 | no |

## Testing

```bash
python manage.py test        # 89 tests
python manage.py makemigrations --check --dry-run
```

Test suite covers, per app: auth (registration/login/logout/profile,
including bad tokens and duplicate accounts), documents (CRUD, upload
validation, ownership, object-level 404s), search/filter/pagination,
notifications (data isolation / IDOR), the full workflow state machine
(role checks, illegal transitions, required reason/comment), comments,
activity log, versions (numbering, blocked-while-under-review,
parent-document scoping), the dashboard aggregate, two end-to-end
tests replicating the brief's 13-step flow (success path + unauthorized
branches), and audit regressions (`documents/tests/test_audit_regressions.py`:
edit-after-changes-requested returns to draft, malformed IDs/payload types
return 404/400 instead of 500, delete removes files only after commit).

## Architecture

```
config/       settings, urls, custom exception handler, pagination class
users/        custom User (role field), JWT auth views
documents/    Category, Document, DocumentVersion, Comment, ActivityLog;
              validators (extension/size/magic-byte), storage (UUID upload
              paths), services (workflow state machine, versioning,
              activity logging), filters, permissions
notifications/  Notification model, bulk-create service, list/mark-read views
dashboard/    single aggregate-query summary endpoint
docs/         Product-Brief.md, rules.md, Build-Plan.md, API.md,
              endpoint-matrix.md, Postman collection
```

Models represent persistence, serializers handle representation +
validation, viewsets handle HTTP orchestration, `services.py` holds the
workflow/versioning business logic (kept out of views so it stays
testable and reusable), `permissions.py` handles authorization,
`filters.py` handles search/filter.

### Models

- `User(AbstractUser)` — `role` (`admin`/`creator`/`reviewer`), enforced by a `CheckConstraint`.
- `Category` — unique `name`; seeded with HR/Finance/Technical/Legal/General via data migration.
- `Document` — title, description, category (FK, PROTECT), file, created_by (FK, PROTECT), status (6-state `CheckConstraint`), current_version, created_at, updated_at. Indexes on `(created_by, status)`, `status`, `-created_at`.
- `DocumentVersion` — document (FK, CASCADE), version_number (unique per document), file, created_by, comment, created_at.
- `Comment` — document, user, comment, created_at.
- `ActivityLog` — document (FK, SET_NULL — survives document deletion), user (FK, SET_NULL), action, description, created_at. Index on `(document, -created_at)`.
- `Notification` — user (FK, CASCADE), message, is_read, created_at. Index on `(user, is_read)`.

### Design decisions

Where the product brief left an implementation detail open, the choice
made and its rationale is recorded in `docs/Build-Plan.md` under "User
decisions" / "Interpretation decisions" — covering reviewer visibility,
category management, PATCH editing rules, version-creation rules, the
`changes_requested → draft` auto-transition, the secure download
endpoints (media is never served publicly), dashboard scope, and
notification triggers.

### Security

- JWT auth (`djangorestframework-simplejwt`) always on; `SessionAuthentication`
  is added only when `DEBUG=True`, so the DRF browsable API and Django admin
  work locally without weakening the production auth surface.
- File uploads: extension whitelist, size limit, and a magic-byte check
  (`%PDF-`, OLE2 header for doc/xls, zip+`PK` header for docx/xlsx, UTF-8/no
  null bytes for txt) so a renamed `.exe` is rejected even with a `.pdf` name.
  Storage paths are UUID-based; original filenames are discarded.
- Every workflow/version-creating operation and every document edit runs in
  `transaction.atomic()` with `select_for_update()` on the document row, so
  concurrent approve/reject/version/edit requests can't race past the status
  check. Document create (document + v1 + activity), comment create (comment +
  activity) and delete (row + activity) are also atomic; stored files are
  removed only after the delete commits.
- Querysets are pre-scoped by role before any object lookup, so requesting
  another user's document/notification/version by ID returns 404, not 403
  (no existence leak).
- `status`, `created_by`, and `current_version` are read-only in the
  document serializer — clients cannot self-approve via payload manipulation.

See `docs/API.md` for the full endpoint reference and
`docs/endpoint-matrix.md` for the per-endpoint auth/role/security/perf
checklist.
