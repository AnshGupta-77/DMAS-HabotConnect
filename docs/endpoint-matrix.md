# Endpoint Test Matrix

Columns: Endpoint | Method | Auth | Roles | Object Access | Valid Input | Invalid Input | Success | Failure | Security Tests | Perf Check | Regression | Docs | Commit

| Endpoint | Method | Auth | Roles | Object Access | Valid | Invalid | Success | Failure | Security | Perf | Regression | Docs | Commit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| /api/auth/register/ | POST | none | any (creator/reviewer only) | n/a | ok | dup/missing/admin-role | 201 | 400 | admin-role rejected | n/a | test_auth.py | API.md | phase1 |
| /api/auth/login/ | POST | none | any | n/a | ok | bad creds | 200 | 401 | brute-force N/A (out of scope) | n/a | test_auth.py | API.md | phase1 |
| /api/auth/login/refresh/ | POST | none | any | n/a | ok | blacklisted/invalid | 200 | 401 | blacklist enforced | n/a | test_auth.py | API.md | phase1 |
| /api/auth/logout/ | POST | required | any | own token only | ok | missing/invalid refresh | 205 | 400/401 | blacklist verified via refresh reuse | n/a | test_auth.py | API.md | phase1 |
| /api/auth/profile/ | GET | required | any | self only | ok | bad token | 200 | 401 | no-auth + bad-token | n/a | test_auth.py | API.md | phase1 |
