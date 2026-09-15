# Endpoint Test Matrix

Columns: Endpoint | Method | Auth | Roles | Object Access | Valid Input | Invalid Input | Success | Failure | Security Tests | Perf Check | Regression | Docs | Commit

| Endpoint | Method | Auth | Roles | Object Access | Valid | Invalid | Success | Failure | Security | Perf | Regression | Docs | Commit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| /api/auth/register/ | POST | none | any (creator/reviewer only) | n/a | ok | dup/missing/admin-role | 201 | 400 | admin-role rejected | n/a | test_auth.py | API.md | phase1 |
| /api/auth/login/ | POST | none | any | n/a | ok | bad creds | 200 | 401 | brute-force N/A (out of scope) | n/a | test_auth.py | API.md | phase1 |
| /api/auth/login/refresh/ | POST | none | any | n/a | ok | blacklisted/invalid | 200 | 401 | blacklist enforced | n/a | test_auth.py | API.md | phase1 |
| /api/auth/logout/ | POST | required | any | own token only | ok | missing/invalid refresh | 205 | 400/401 | blacklist verified via refresh reuse | n/a | test_auth.py | API.md | phase1 |
| /api/auth/profile/ | GET | required | any | self only | ok | bad token | 200 | 401 | no-auth + bad-token | n/a | test_auth.py | API.md | phase1 |
| /api/documents/ | POST | required | creator, admin | n/a | ok | missing fields/bad ext/spoofed/oversized | 201 | 400/401/403 | reviewer-upload rejected, unauth rejected | select_related on list | test_documents.py | API.md | phase2 |
| /api/documents/ | GET | required | any | role-scoped queryset | ok | n/a | 200 | 401 | role scoping verified | select_related, paginated | test_documents.py | API.md | phase2 |
| /api/documents/{id}/ | GET | required | any | 404 outside scope | ok | bad id | 200 | 404 | IDOR: other creator's doc | select_related | test_documents.py | API.md | phase2 |
| /api/documents/{id}/ | PATCH | required | owner, admin | 403 non-owner | ok | status field ignored | 200 | 403 | status manipulation ignored, approved-doc edit blocked | n/a | test_documents.py | API.md | phase2 |
| /api/documents/{id}/ | DELETE | required | owner(draft), admin | 403 non-draft for creator | ok | n/a | 204 | 403 | non-owner delete blocked | n/a | test_documents.py | API.md | phase2 |
| /api/documents/{id}/download/ | GET | required | same as retrieve | 404 outside scope | ok | n/a | 200 | 404 | IDOR on download | n/a | test_documents.py | API.md | phase2 |
| /api/documents/?status=&category=&created_by=&search=&ordering= | GET | required | any | role-scoped | ok | invalid status | 200 | 400 | invalid enum rejected | assertNumQueries(3) constant | test_filters.py | API.md | phase3 |
