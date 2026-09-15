DMAS — Development & Engineering Rules

1. Purpose

This document defines the mandatory rules for building, testing, reviewing, documenting, securing, optimizing, and maintaining the Document Management & Approval System (DMAS).

These rules apply to the complete implementation described in product-brief.md. The product brief defines the required product behavior; this file defines the engineering discipline that must be followed while implementing that behavior.

Rule priority:

Security and data integrity

Functional correctness and product requirements

Authorization and workflow integrity

Test coverage and verification

Performance and reliability

Maintainability and clean architecture

Documentation and Git history

No feature is considered complete until all applicable requirements in this file have been satisfied.

2. Product Requirement Compliance

2.1 Source of Truth

product-brief.md is the primary functional specification.

Do not silently remove, weaken, reinterpret, or skip a requirement from the product brief.

If an implementation decision conflicts with the product brief, stop and resolve the conflict before proceeding.

Any intentional scope change must be explicitly documented.

Do not add unnecessary product features merely because they are technically interesting.

2.2 Required Core Capabilities

The implementation must cover:

User registration and login.

Authentication and protected APIs.

Admin, Creator, and Reviewer/Approver roles.

Document creation and management.

File uploads.

Document categories.

Document status workflow.

Submission for review.

Review.

Approval.

Rejection.

Change requests.

Comments.

Basic document versions.

Search and filtering.

Pagination.

Role-based permissions.

Activity/audit logging.

In-application notifications.

Dashboard information.

Validation.

Consistent API error handling.

Automated tests.

Clean and modular Django/DRF structure.

3. Architecture Rules

3.1 Technology

The system must use the intended stack:

Python 3.x

Django

Django REST Framework

PostgreSQL

JWT or Token Authentication

Git

Postman for API verification where appropriate

3.2 Separation of Responsibilities

Code must have clear responsibilities.

Models represent persistent data and domain relationships.

Serializers handle API representation and serializer-level validation.

Views/viewsets handle HTTP/API orchestration.

Permission classes handle authorization.

Services contain reusable business operations when business logic would otherwise make views difficult to maintain.

Filters handle search/filter behavior.

Tests verify behavior.

Configuration must not be mixed with business logic.

Do not put large amounts of unrelated business logic directly into views.

3.3 Maintainability

Prefer simple, readable implementations.

Avoid unnecessary abstractions.

Avoid premature generic frameworks or helper layers.

Keep modules focused.

Use meaningful names.

Keep functions reasonably small.

Avoid duplicated business rules.

Reuse existing utilities when they already solve the problem correctly.

Do not create an abstraction unless it has a clear purpose.

Preserve a structure that another developer can understand without reverse-engineering the entire application.

4. No Dead Code Rule

Dead code must not be generated or intentionally retained.

This includes:

Unused imports.

Unused functions.

Unused classes.

Unused variables.

Unreachable branches.

Abandoned endpoints.

Duplicate implementations.

Commented-out obsolete implementations.

Unused serializers.

Unused services.

Unused models.

Unused configuration.

Temporary debugging code.

Unused dependencies.

Placeholder code that has no current purpose.

Before completing a feature:

Identify newly created code that is not used.

Remove obsolete implementations.

Remove unused imports.

Remove debugging statements.

Remove temporary files.

Run lint/static checks where configured.

Verify that the final implementation contains only required or intentionally reusable code.

Do not keep code merely because it might be useful later.

5. Database Rules

5.1 Relational Integrity

The database must correctly represent:

Users.

Documents.

Document versions.

Comments.

Activity logs.

Notifications.

Relationships must use appropriate foreign keys and constraints.

5.2 Data Integrity

Required fields must be enforced.

Invalid relationships must be rejected.

Version records must belong to the correct document.

Activity records must reference the correct document/user where applicable.

Notifications must belong to the correct recipient.

Status values must be constrained to supported states.

Version numbers must be generated consistently.

5.3 Migrations

Every schema change must have a proper Django migration.

Never modify production database structure manually when the change should be represented by a migration.

Migration files must be committed to Git.

Test migrations before considering a schema feature complete.

Do not leave migration files generated locally but uncommitted.

5.4 Query Efficiency

Avoid:

N+1 queries.

Repeated identical database queries.

Loading unnecessary fields.

Unbounded list queries.

Fetching entire related collections when only a small subset is required.

Use appropriate:

select_related()

prefetch_related()

database indexes

filtered querysets

pagination

aggregation where appropriate

Do not add indexes blindly. Add them when they support actual filtering, lookup, uniqueness, or performance requirements.

6. Authentication Rules

6.1 Protected APIs

All protected document and user-specific APIs must require authentication.

Unauthenticated requests must not gain access through:

Missing permission classes.

Incorrect URL configuration.

Alternate HTTP methods.

Object-level authorization gaps.

Serializer manipulation.

Query parameter manipulation.

6.2 Credentials

Passwords must never be stored in plaintext.

Never log passwords, tokens, authentication headers, or secrets.

Never hard-code credentials.

Secrets must be supplied through appropriate configuration/environment mechanisms.

Authentication errors must not expose sensitive implementation details.

6.3 Login and Registration

Validate:

Required fields.

Credential correctness.

Duplicate accounts according to the selected user identity rules.

Invalid authentication attempts.

Unauthorized access.

7. Authorization Rules

Authentication answers "Who are you?"

Authorization answers "What are you allowed to do?"

Both must be enforced.

7.1 Roles

The system must support:

Admin

Document Creator

Reviewer/Approver

7.2 Permission Enforcement

Permissions must be enforced server-side.

Never rely on the frontend to prevent unauthorized actions.

Examples:

Creator cannot approve.

Creator cannot reject.

Creator cannot review.

Reviewer cannot upload when the product rules prohibit it.

Reviewer cannot modify creator-owned documents outside permitted workflow actions.

Users cannot access documents they are not authorized to access.

Users cannot manipulate an ID in the URL to access another user's protected data.

Admin has the administrative capabilities defined by the product brief.

7.3 Object-Level Security

Every endpoint operating on a document must verify access to that specific document.

Never assume that:

authenticated user = authorized for every object

Authorization must be checked against both:

the user's role

the target object's ownership/access rules

8. Document Rules

Every document must maintain the required information:

Document ID

Title

Description

Category

File

Created By

Status

Version

Created Date

Updated Date

8.1 Ownership

The creator must be correctly associated with the document.

Users must not be able to change document ownership through API payload manipulation.

Ownership must be determined server-side where appropriate.

8.2 Editing

Users may edit only documents they are authorized to edit.

Approved documents must not be silently overwritten when a new version is required.

Status-dependent editing rules must be enforced server-side.

9. File Upload Security Rules

Supported assessment formats are:

PDF

DOC/DOCX

XLS/XLSX

TXT

9.1 Validation

Every upload must validate:

File exists.

File type is allowed.

File size is within the configured limit.

The request is authorized.

The file can be safely handled by the configured storage mechanism.

9.2 Security

Do not trust only a filename or client-provided MIME type.

Where practical, validate file characteristics using server-side checks appropriate to the supported file formats.

Prevent:

Executable uploads where not supported.

Path traversal.

Arbitrary filesystem paths.

Unsafe filenames.

Unauthorized file replacement.

Unauthorized file retrieval.

9.3 Storage

Do not expose raw filesystem paths through API responses.

Do not allow users to choose arbitrary storage locations.

Keep file storage configuration separate from business logic.

Ensure uploaded files cannot overwrite unrelated files.

10. Workflow Rules

The document lifecycle must be treated as a controlled state machine.

Primary flow:

Draft
  ↓
Submitted
  ↓
Under Review
  ↓
Approved

Alternative flows:

Under Review
  ↓
Rejected

and:

Under Review
  ↓
Changes Requested
  ↓
Draft

10.1 Valid Transitions

Only valid state transitions may occur.

Examples:

Draft → Submitted: allowed.

Submitted → Under Review: allowed.

Under Review → Approved: allowed.

Under Review → Rejected: allowed.

Under Review → Changes Requested: allowed.

Changes Requested → Draft: allowed.

Invalid transitions must be rejected.

10.2 Direct Status Manipulation

Do not allow clients to bypass workflow rules by sending:

{
  "status": "approved"
}

or equivalent payloads.

Workflow actions must be controlled by dedicated server-side operations.

10.3 Approval

Only authorized reviewers/admins may approve.

A creator must never be able to approve their own document simply by manipulating the request.

10.4 Rejection

A rejection reason is mandatory.

Empty or whitespace-only reasons are invalid.

10.5 Change Requests

A change request must include an explanatory comment describing what needs to change.

11. Review Rules

The review endpoint must:

Require authentication.

Require reviewer/admin authorization.

Operate only on documents in an appropriate state.

Record the review activity.

Preserve the document's workflow integrity.

Not silently modify unrelated document data.

Review actions must be deterministic and auditable.

12. Comment Rules

Comments must:

Belong to a valid document.

Belong to an authenticated user.

Contain non-empty content.

Respect document access permissions.

Record creation time.

Reject:

Empty comments.

Whitespace-only comments.

Comments against inaccessible documents.

Comment creation must not permit users to impersonate another user.

13. Version Management Rules

When an approved document needs modification, create a new version instead of replacing the approved version.

Each version must contain:

Version ID

Document

Version Number

File

Created By

Created Date

Comments

13.1 Version Integrity

A version must belong to exactly the intended document.

Version numbers must be generated safely.

Clients must not be trusted to arbitrarily assign conflicting version numbers.

Existing approved versions must remain available according to the assessment requirements.

Advanced comparison/restoration is outside the required scope unless explicitly added later.

14. Activity / Audit Rules

Important actions must create activity records.

At minimum:

Document Created

Document Updated

Document Submitted

Document Reviewed

Document Approved

Document Rejected

Comment Added

Version Created

Document Deleted

Activity entries should identify the relevant:

User

Action

Document

Description where appropriate

Timestamp

Activity creation should happen as part of the same business operation where consistency requires it.

Do not claim an action occurred in the audit log if the actual business operation failed.

15. Notification Rules

Notifications must be generated for the required workflow events.

Examples:

Submitted → reviewer notification.

Approved → creator notification.

Changes Requested → creator notification.

Notifications must contain:

Notification ID

User

Message

Read/unread state

Created date

Users must not be able to mark another user's notification as read through ID manipulation.

Email notifications remain optional unless the scope is explicitly expanded.

16. Search and Filtering Rules

Document search must support the required fields:

Title

Category

Status

Created by

16.1 Query Safety

Never construct unsafe raw SQL from user input.

Use Django ORM/query parameterization.

Validate filter values.

Handle invalid query parameters consistently.

16.2 Performance

Search must avoid unnecessary database scans where practical.

Use appropriate indexes and query construction based on actual access patterns.

Do not retrieve all documents and filter them in Python when the database can perform the filtering efficiently.

17. Pagination Rules

Document listing APIs must be paginated.

Expected response structure:

{
  "count": 0,
  "next": null,
  "previous": null,
  "results": []
}

Rules:

Never return an unbounded document collection.

Apply sensible maximum page sizes.

Do not allow clients to request an unlimited page.

Validate pagination parameters.

Ensure pagination queries remain efficient.

18. API Design Rules

All APIs must follow REST principles and consistent conventions.

Required endpoint groups include:

Authentication

POST /api/auth/register/
POST /api/auth/login/
POST /api/auth/logout/
GET  /api/auth/profile/

Documents

POST   /api/documents/
GET    /api/documents/
GET    /api/documents/{id}/
PATCH  /api/documents/{id}/
DELETE /api/documents/{id}/

Workflow

POST /api/documents/{id}/submit/
POST /api/documents/{id}/review/
POST /api/documents/{id}/approve/
POST /api/documents/{id}/reject/
POST /api/documents/{id}/request-changes/

Comments

POST /api/documents/{id}/comments/
GET  /api/documents/{id}/comments/

Versions

POST /api/documents/{id}/versions/
GET  /api/documents/{id}/versions/
GET  /api/documents/{id}/versions/{version_id}/

Activity

GET /api/documents/{id}/activity/

Notifications

GET   /api/notifications/
PATCH /api/notifications/{id}/read/

Dashboard

GET /api/dashboard/

Do not create duplicate endpoints that perform the same operation without a documented reason.

19. HTTP Status Rules

Use appropriate HTTP status codes.

At minimum:

200 OK

201 Created

400 Bad Request

401 Unauthorized

403 Forbidden

404 Not Found

Use the most semantically appropriate response for each operation.

Errors must be:

predictable

structured

safe

useful to API consumers

Never expose:

stack traces

SQL queries

filesystem paths

secret values

internal credentials

sensitive server configuration

in normal production API responses.

20. Validation Rules

Validation must happen at the API boundary and at appropriate domain/database boundaries.

Required validation includes:

Documents

Title required.

Category required.

File required when creating/uploading.

Supported file type.

File size limit.

Approval

Authorized reviewer/admin only.

Correct workflow state.

Rejection reason mandatory for rejection.

Comments

Comment cannot be empty.

Versions

Correct parent document.

Correct version numbering.

Correct authorization.

Validation must not depend exclusively on frontend behavior.

Malformed input must never produce a 500. Payload fields read directly from request data must be type-checked (a non-string reason/comment returns 400), and URL path parameters must be constrained to their expected format (a non-numeric ID returns 404).

21. Security Testing Rules

Every endpoint must be security-tested before the feature is considered complete.

For every endpoint, test at minimum where applicable:

Authentication

No authentication.

Valid authentication.

Invalid authentication.

Expired/invalid token if the selected authentication mechanism supports it.

Authorization

Test:

Admin.

Creator.

Reviewer.

Wrong role.

Different user's object.

Object owner.

Non-owner.

Attempted privilege escalation.

Input Security

Test:

Missing required fields.

Empty values.

Whitespace-only values.

Invalid IDs.

Non-existent IDs.

Invalid enum/status values.

Unexpected fields.

Oversized input.

Malformed payloads.

Invalid file types.

Oversized files.

HTTP Method Security

Verify unsupported methods cannot bypass intended authorization or business logic.

Object Access

For every object-based endpoint, verify that changing:

{id}

cannot expose or modify another user's protected data.

Workflow Security

Attempt illegal transitions deliberately.

Examples:

Creator → approve.

Creator → reject.

Draft → approve.

Approved → approve again.

Rejected → approve without the required workflow.

Unauthorized user → review.

Every invalid attempt must fail safely.

22. Endpoint Performance Rules

Every endpoint must be checked for speed and efficient data collection.

The goal is not premature micro-optimization. The goal is to prevent obvious inefficient implementation.

Check for:

N+1 queries.

Duplicate queries.

Unnecessary serialization work.

Unbounded querysets.

Excessive joins.

Repeated database access.

Loading unused related objects.

Expensive Python-side filtering.

Large unnecessary response payloads.

For collection/list endpoints:

Pagination is mandatory where applicable.

Query only what is needed.

Use efficient filtering.

Use appropriate relation loading.

Avoid serializing unnecessary nested data.

For detail endpoints:

Avoid unnecessary queries.

Fetch required relations efficiently.

Avoid returning unrelated data.

For dashboard endpoints:

Prefer database aggregation/counts over loading every document into Python.

Performance improvements must not weaken authorization or data correctness.

23. API Response Rules

Responses should be:

Consistent.

Predictable.

Minimal enough for the operation.

Free of sensitive internal information.

Stable across normal requests.

Do not expose internal database implementation details unless intentionally part of the API contract.

Avoid returning enormous nested structures when a small response is sufficient.

24. Transaction and Consistency Rules

Operations that modify multiple related records must consider transaction boundaries.

Examples:

Approving a document and recording its activity.

Rejecting a document and recording its activity.

Requesting changes and creating the related notification/activity.

Creating a version and updating current-version information.

If these operations must succeed together, use an appropriate database transaction.

Do not leave the database in a partially updated state when a related required operation fails.

Irreversible side effects outside the database, such as deleting stored files, must run only after the transaction commits (for example with transaction.on_commit()), so a rolled-back operation never leaves records pointing at missing files.

25. Concurrency Rules

Where two requests could modify the same document or version simultaneously, consider race conditions.

Pay particular attention to:

Approval.

Rejection.

Status transitions.

Version number generation.

Current-version updates.

Concurrent document updates.

Do not assume requests always arrive sequentially.

26. Testing Rules

Testing is mandatory, not optional.

Minimum required coverage from the product brief includes:

Authentication

Registration.

Login.

Unauthorized access.

Documents

Create.

Retrieve.

Update.

Delete.

Workflow

Submit.

Approve.

Reject.

Request changes.

Permissions

Creator cannot approve.

Reviewer cannot upload.

Unauthorized users cannot access protected APIs.

Validation

Invalid file.

Missing required fields.

Invalid status transition.

Target:

15–25 meaningful tests minimum.

The target is a baseline, not a ceiling. Add tests when additional complexity requires them.

27. Test Quality Rules

Do not write tests merely to increase the test count.

Every test must verify meaningful behavior.

Prefer tests that prove:

Correct behavior.

Incorrect behavior is rejected.

Permissions work.

Workflow transitions are enforced.

Data isolation works.

Validation works.

Errors are returned correctly.

Related records are created correctly.

Regression bugs remain fixed.

Avoid:

Tests that only exercise code without assertions.

Duplicate tests with no additional value.

Tests coupled unnecessarily to implementation details.

28. Endpoint Test Matrix

Maintain an endpoint test checklist throughout development.

For each endpoint record:

Endpoint
HTTP Method
Authentication Required
Allowed Roles
Object Access Rules
Valid Input
Invalid Input
Expected Success Status
Expected Failure Status
Security Tests
Performance Check
Regression Test
Documentation Updated
Git Commit

An endpoint is not considered complete until all applicable fields have been verified.

29. Regression Testing Rules

After changing an existing feature:

Run the tests for the changed feature.

Run related tests.

Run the complete test suite before merging/completing the feature when practical.

Confirm that existing API behavior has not unintentionally broken.

Re-test authorization if the change affects permissions, querysets, serializers, or workflow logic.

Never assume that a small code change has a small impact.

30. Documentation Rules

Every completed feature must update every required document.

Documentation is part of feature completion, not a final optional task.

After implementation, update all documents affected by the change, including as applicable:

product-brief.md if requirements changed.

rules.md if a new engineering rule was discovered or required.

API documentation.

README.

Setup documentation.

Environment/configuration documentation.

Database/model documentation.

Testing documentation.

Endpoint collections/examples.

Changelog/release notes where maintained.

Architecture documentation where architecture changed.

Do not leave documentation describing an older system after the implementation has changed.

30.1 Documentation Accuracy

Documentation must reflect the actual implementation.

Never document:

An endpoint that does not exist.

A feature that is not implemented.

A permission that is not enforced.

A configuration variable that is not used.

A workflow that differs from actual behavior.

31. Git Rules

Git history must represent meaningful development progress.

31.1 Commit After Features

After each completed feature:

Implement the feature.

Test it.

Perform security checks.

Perform relevant performance checks.

Remove dead code.

Update required documentation.

Review the diff.

Commit the completed work.

Do not accumulate a large number of unrelated completed features into one final commit.

31.2 Commit Scope

Each commit should represent a coherent change.

Good examples:

feat: add document creation and upload
feat: implement document submission workflow
feat: add reviewer approval and rejection
test: add document permission coverage
perf: optimize document list queries
docs: update API documentation
fix: prevent unauthorized document access

Avoid commits such as:

update
changes
final
stuff
fixes
asdf

31.3 Before Every Commit

Run an appropriate pre-commit checklist:

[ ] Feature works
[ ] Tests pass
[ ] Security checks pass
[ ] Performance checked
[ ] Dead code removed
[ ] Documentation updated
[ ] No secrets committed
[ ] No accidental files committed
[ ] Database migrations included if required
[ ] Git diff reviewed

32. Git Safety Rules

Never commit:

Passwords.

API keys.

JWT secrets.

Cloud credentials.

Database credentials.

Private certificates.

Local secret files.

Personal data.

Debug dumps.

Uploaded user documents.

Temporary build artifacts.

Use .gitignore appropriately.

Before committing, inspect:

git status
git diff

and review staged changes before creating the commit.

33. Dependency Rules

Do not add a dependency without a reason.

Before adding a package:

Confirm the existing stack cannot reasonably solve the requirement.

Confirm the package is actually needed.

Check compatibility.

Add it to the correct dependency file.

Document configuration if required.

Test the application after installation.

Commit the dependency change with the feature that requires it.

Remove dependencies that are no longer used.

34. Configuration Rules

Configuration must be environment-aware.

Do not hard-code:

Database credentials.

Secret keys.

Authentication secrets.

Production hostnames.

Private credentials.

Environment-specific sensitive settings.

Separate development/test/production configuration appropriately.

The application must fail clearly when a required production configuration is missing rather than silently using an unsafe fallback.

35. Error and Logging Rules

Logging must help diagnose problems without leaking sensitive information.

Never log:

Passwords.

Authentication tokens.

Authorization headers.

Secret keys.

Private file contents.

Sensitive user information unnecessarily.

Do not use print() as permanent application logging.

Remove temporary debugging output before feature completion.

36. API Documentation Rules

Every implemented endpoint must have enough documentation to explain:

Method.

Path.

Authentication requirements.

Allowed roles.

Request format.

Required fields.

Optional fields.

Response format.

Validation errors.

Permission errors.

Workflow restrictions where applicable.

If Swagger/OpenAPI is used, keep it synchronized with the actual API.

37. Code Review Rules

Before declaring a feature complete, review the code as if another developer will maintain it.

Check:

Is the code understandable?

Is the business logic in the correct layer?

Are permissions explicit?

Are queries efficient?

Is validation complete?

Are errors handled?

Are transactions required?

Are race conditions possible?

Is there duplicated logic?

Is there dead code?

Are tests meaningful?

Is documentation accurate?

Are there security vulnerabilities?

Are there unnecessary dependencies?

38. Scope Control Rules

The assessment is intentionally focused.

Do not introduce unnecessary advanced systems such as:

Microservices.

Event-driven architecture.

Message queues.

Complex distributed systems.

Advanced AI.

Advanced version comparison.

Version restoration.

Immutable enterprise audit infrastructure.

Legal compliance platforms.

IP tracking.

Audit analytics.

unless the project scope is explicitly expanded.

The goal is a complete, correct, secure, maintainable implementation of DMAS—not an unnecessarily complex enterprise platform.

39. Feature Completion Definition

A feature is DONE only when all applicable conditions are satisfied:

[ ] Product requirement implemented
[ ] Database changes implemented correctly
[ ] API implemented
[ ] Authentication verified
[ ] Authorization verified
[ ] Object-level access verified
[ ] Input validation implemented
[ ] Error handling implemented
[ ] Workflow rules verified
[ ] Security tests completed
[ ] Performance/query efficiency checked
[ ] Automated tests added
[ ] Regression tests pass
[ ] Dead code removed
[ ] Debug code removed
[ ] Documentation updated
[ ] API documentation updated if applicable
[ ] Migrations created and tested if applicable
[ ] Git diff reviewed
[ ] Git commit created

If an applicable item is incomplete, the feature is not complete.

40. Complete System Verification

Before final delivery, perform a complete end-to-end verification.

Required flow:

1. User registers
       ↓
2. User logs in
       ↓
3. Creator uploads document
       ↓
4. Document is saved as Draft
       ↓
5. Creator submits document
       ↓
6. Reviewer sees submitted document
       ↓
7. Reviewer reviews document
       ↓
8. Reviewer adds comment
       ↓
9. Reviewer approves/rejects/requests changes
       ↓
10. Creator receives notification
       ↓
11. Approved document can be viewed
       ↓
12. Creator creates a new version when required
       ↓
13. Activity is recorded

Verify both:

the successful path

invalid/unauthorized paths

The system must be tested as a complete workflow, not merely as isolated endpoints.

41. Final Security Audit

Before delivery, verify the entire application for:

Authentication bypass.

Authorization bypass.

IDOR/object-level access vulnerabilities.

Privilege escalation.

Unauthorized status changes.

Unauthorized document access.

Unsafe file uploads.

Path traversal.

Injection risks.

Unsafe query construction.

Sensitive information exposure.

Secret leakage.

Excessive API responses.

Missing pagination.

Rate/abuse concerns where applicable.

Improper error disclosure.

Race conditions around workflow/version operations.

Every discovered vulnerability must be fixed and regression-tested before final delivery.

42. Final Performance Audit

Before delivery:

Inspect expensive endpoints.

Inspect document list queries.

Inspect search/filter queries.

Inspect dashboard queries.

Check for N+1 queries.

Check pagination.

Check unnecessary serialization.

Check unnecessary database access.

Check large response payloads.

Check file handling behavior.

Do not optimize blindly. Measure or inspect the actual bottleneck and make targeted improvements.

43. Final Code Quality Audit

Before delivery:

[ ] No dead code
[ ] No unused imports
[ ] No debugging statements
[ ] No unnecessary dependencies
[ ] No duplicated business logic
[ ] No hard-coded secrets
[ ] No accidental local files
[ ] No TODOs representing unfinished required work
[ ] Clean project structure
[ ] Meaningful names
[ ] Consistent API behavior
[ ] Tests passing
[ ] Documentation current

44. Final Git Audit

Before final submission:

git status
git diff
git log --oneline

Confirm:

All intended work is committed.

No required files are untracked.

No secrets are committed.

Migrations are committed.

Tests are committed.

Documentation is committed.

Feature history is understandable.

No unrelated files are included.

The working tree should be clean unless there is a deliberately documented reason for uncommitted work.

45. Non-Negotiable Engineering Principles

The following principles apply throughout the project:

Security before convenience.

Server-side authorization is mandatory.

Never trust client-controlled permissions or status values.

Every endpoint must be tested.

Every endpoint must receive applicable security checks.

Every endpoint must receive an efficiency/performance review.

Do not generate dead code.

Do not retain obsolete code without a documented reason.

Every completed feature must update every affected document.

Every completed feature must have meaningful tests.

Every completed feature must have an appropriate Git commit.

Do not commit secrets.

Do not silently change requirements.

Do not over-engineer the assessment.

Do not sacrifice correctness for speed.

Do not sacrifice security for convenience.

Do not claim a feature is complete until its verification is complete.

Keep implementation, documentation, tests, and Git history synchronized.

46. Completion Standard

The DMAS project is considered complete only when:

The complete product scope in product-brief.md is implemented.

All required APIs work.

Authentication works.

Role-based and object-level authorization works.

File handling is validated and secured.

Document workflow transitions are enforced.

Comments, versions, activities, notifications, and dashboard behavior work.

Search, filtering, and pagination work.

Validation and error handling are consistent.

The required test suite passes.

Every endpoint has been security-tested.

Every endpoint has received an efficiency/performance check.

No dead code remains.

No unfinished required implementation remains.

All affected documentation is current.

All required migrations are committed.

Git history contains meaningful feature/fix/test commits.

The complete end-to-end workflow has been verified.

Final security, performance, code-quality, documentation, and Git audits have been completed.

No feature is complete merely because its code exists. A feature is complete only after implementation, testing, security verification, optimization review, documentation, cleanup, and Git commit are all complete.