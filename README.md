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
pip install -r requirements-dev.txt

cp .env.example .env   # edit values for your machine

createdb dmas
python manage.py migrate
python manage.py createsuperuser   # admin role
python manage.py runserver
```

## Environment variables

| Variable | Purpose | Required |
|---|---|---|
| `DJANGO_SECRET_KEY` | Django secret key | yes in production |
| `DEBUG` | `True`/`False` | no (default `False`) |
| `ALLOWED_HOSTS` | comma-separated hosts | in production |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | PostgreSQL connection | yes |
| `MAX_UPLOAD_SIZE_MB` | max upload size, default 10 | no |

## Testing

```bash
python manage.py test
ruff check .
```

## Design decisions

See `docs/Build-Plan.md` for the full list of interpretation decisions made
where the product brief left an implementation detail open (reviewer
visibility, category management, editing rules, version rules, download
endpoints, dashboard scope, notification triggers).

## Architecture

See `docs/API.md` for the endpoint reference and `docs/endpoint-matrix.md`
for the per-endpoint test/security/performance checklist.
