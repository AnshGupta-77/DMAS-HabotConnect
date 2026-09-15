Product Brief — Document Management & Approval System

Software Requirements Specification (SRS)

1. Project Overview

The Document Management & Approval System (DMAS) is a web-based application that allows users to upload, manage, review, approve, and track documents.
The purpose of this project is to assess the recruit's understanding of:

Python and Django

Django REST Framework

Database design

REST API development

Authentication and authorization

File handling

Basic workflow implementation

API validation

Search and filtering

Basic notifications

Clean project structure

The project should be implemented as a Django + Django REST Framework backend.

2. Main Objective

The system should allow users to:

Register/Login

Upload documents

Add document information

View documents

Search and filter documents

Submit documents for review

Review documents

Approve or reject documents

Add comments

Maintain basic document versions

Track document activity

View basic dashboard information

3. User Roles

The system should support three basic roles.

3.1 Admin

Admin can:

View all documents

View all users

Manage document categories

Delete documents

View audit/activity records

3.2 Document Creator

Creator can:

Upload documents

Edit their own documents

Submit documents for review

Create a new version

View comments

View document status

3.3 Reviewer/Approver

Reviewer can:

View submitted documents

Review documents

Add comments

Approve documents

Reject documents

Request changes

4. Authentication

Implement basic user authentication.

Required APIs

POST /api/auth/register/
POST /api/auth/login/
POST /api/auth/logout/
GET  /api/auth/profile/

The API should prevent unauthenticated users from accessing protected document APIs.
Use an appropriate authentication mechanism such as:

Token Authentication

JWT Authentication

5. Document Management

Users should be able to create and manage documents.

Document Information

Each document should contain:

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

Basic Document Categories

Examples:

HR
Finance
Technical
Legal
General

Required APIs

POST   /api/documents/
GET    /api/documents/
GET    /api/documents/{id}/
PATCH  /api/documents/{id}/
DELETE /api/documents/{id}/

6. File Upload

Users should be able to upload a document.
For the assessment, support common formats such as:

PDF
DOC/DOCX
XLS/XLSX
TXT

The system should perform basic validation:

File is provided

File type is allowed

File size is within the configured limit

The actual file can be stored using Django's file storage mechanism.

7. Document Status

Each document should have a simple status workflow.

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

or

Under Review
      ↓
Changes Requested
      ↓
    Draft

Status Rules

A creator should not be able to directly mark a document as Approved.
Only an authorized reviewer/approver should be able to approve or reject a submitted document.

8. Document Submission

A creator should be able to submit a document for review.

API

POST /api/documents/{id}/submit/

When submitted:

Draft → Submitted

The document can then move to:

Submitted → Under Review

9. Review & Approval

A reviewer should be able to review a submitted document.

APIs

POST /api/documents/{id}/review/
POST /api/documents/{id}/approve/
POST /api/documents/{id}/reject/
POST /api/documents/{id}/request-changes/

Approve

Under Review → Approved

Reject

Under Review → Rejected

A rejection reason should be required.
Example:

Reason:
"Please update the project description."

Request Changes

Under Review → Changes Requested

The reviewer should provide a comment explaining what needs to be changed.

10. Comments

Users should be able to add comments to documents.
A comment should contain:

Comment ID
Document
User
Comment
Created Date

APIs

POST /api/documents/{id}/comments/
GET  /api/documents/{id}/comments/

Example:

Document: Project Proposal
User: John
Comment: Please update the budget section.

11. Basic Version Management

When a user modifies an approved document, they should create a new version instead of replacing the approved version.
Example:

Version 1.0
Initial document

Version 2.0
Updated document

Version Information

Version ID
Document
Version Number
File
Created By
Created Date
Comments

APIs

POST /api/documents/{id}/versions/
GET  /api/documents/{id}/versions/
GET  /api/documents/{id}/versions/{version_id}/

For this assessment, advanced features such as version comparison and restoration are not required.

12. Search & Filtering

Users should be able to search documents.

Search By

Document title

Category

Status

Created by

Example:

GET /api/documents/?search=policy

Filtering

Examples:

GET /api/documents/?status=approved

GET /api/documents/?category=HR

GET /api/documents/?created_by=5

Pagination should be implemented for the document list API.

13. Permissions

Implement basic role-based permissions.

Example

Action

Admin

Creator

Reviewer

View documents

Yes

Own documents

Assigned/available documents

Upload

Yes

Yes

No

Edit

Yes

Own documents

No

Delete

Yes

Own drafts

No

Submit

Yes

Yes

No

Review

Yes

No

Yes

Approve

Yes

No

Yes

Reject

Yes

No

Yes

Comment

Yes

Yes

Yes

The recruit should implement these permissions using Django REST Framework permission classes.

14. Activity / Audit Log

The system should maintain a basic activity log.
Record important actions such as:

Document Created
Document Updated
Document Submitted
Document Reviewed
Document Approved
Document Rejected
Comment Added
Version Created
Document Deleted

Example:

User: John
Action: Document Approved
Document: DOC-1001
Date: 14-Sep-2026

API

GET /api/documents/{id}/activity/

Advanced requirements such as immutable audit storage, IP tracking, legal compliance, and audit analytics are not required.

15. Notifications

Implement basic in-application notifications.
Examples:
When a document is submitted:

"You have a document waiting for review."

When a document is approved:

"Your document has been approved."

When changes are requested:

"Changes have been requested for your document."

Notification Information

Notification ID
User
Message
Read/Unread
Created Date

APIs

GET   /api/notifications/
PATCH /api/notifications/{id}/read/

Email notifications are optional and not required for the basic assessment.

16. Dashboard

Create a simple dashboard API.
The dashboard should provide:

Total Documents
Draft Documents
Submitted Documents
Pending Reviews
Approved Documents
Rejected Documents

API

GET /api/dashboard/

Example response:

{
    "total_documents": 25,
    "draft_documents": 5,
    "submitted_documents": 6,
    "pending_reviews": 4,
    "approved_documents": 8,
    "rejected_documents": 2
}

17. Database Design

The recruit should design an appropriate relational database.
Suggested entities:

User
  |
  └── Document
        |
        ├── DocumentVersion
        ├── Comment
        ├── ActivityLog
        └── Notification

Suggested Models

User

Use Django's built-in user model or a custom user model.

Document

id
title
description
category
file
created_by
status
current_version
created_at
updated_at

DocumentVersion

id
document
version_number
file
created_by
comment
created_at

Comment

id
document
user
comment
created_at

ActivityLog

id
document
user
action
description
created_at

Notification

id
user
message
is_read
created_at

18. API Requirements

All APIs should follow REST principles.
The recruit should provide:

Authentication

POST /api/auth/register/
POST /api/auth/login/
GET  /api/auth/profile/

Documents

POST   /api/documents/
GET    /api/documents/
GET    /api/documents/{id}/
PATCH  /api/documents/{id}/
DELETE /api/documents/{id}/

Workflow

POST /api/documents/{id}/submit/
POST /api/documents/{id}/review/
POST /api/documents/{id}/approve/
POST /api/documents/{id}/reject/
POST /api/documents/{id}/request-changes/

Comments

POST /api/documents/{id}/comments/
GET  /api/documents/{id}/comments/

Versions

POST /api/documents/{id}/versions/
GET  /api/documents/{id}/versions/

Activity

GET /api/documents/{id}/activity/

Notifications

GET /api/notifications/
PATCH /api/notifications/{id}/read/

Dashboard

GET /api/dashboard/

19. Validation Requirements

The application should implement appropriate validation.
Examples:

Document

Title is required

Category is required

File is required

File type must be supported

File size must be within the limit

Approval

Only reviewers/admins can approve

Only documents under review can be approved

Rejection reason is mandatory

Comments

Comment cannot be empty

Version

Version must belong to the correct document

Version number should be generated correctly

20. Error Handling

APIs should return appropriate HTTP status codes.
Examples:

200 OK
201 Created
400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found

Example error:

{
    "error": "You do not have permission to approve this document."
}

21. Pagination

The document listing API should support pagination.
Example:

GET /api/documents/?page=1&page_size=10

The response should contain:

count
next
previous
results



22. Testing Requirements

The recruit should write tests for the important functionality.
Minimum tests should cover:

Authentication

Registration

Login

Unauthorized access

Documents

Create document

Retrieve document

Update document

Delete document

Workflow

Submit document

Approve document

Reject document

Request changes

Permissions

Creator cannot approve

Reviewer cannot upload

Unauthorized user cannot access protected APIs

Validation

Invalid file

Missing required fields

Invalid status transition

A reasonable target is 15–25 meaningful test cases.

23. Recommended Technology Stack

The project should use:

Python 3.x
Django
Django REST Framework
PostgreSQL
JWT / Token Authentication
Git
Postman



25. Project Structure

A clean Django project structure is expected.
Example:

document_management/
│
├── manage.py
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── ...
│
├── users/
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── permissions.py
│
├── documents/
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   ├── permissions.py
│   ├── filters.py
│   └── services.py
│
├── notifications/
│   ├── models.py
│   ├── serializers.py
│   └── views.py
│
└── tests/

The recruit does not have to follow this exact structure, but the code should be modular and maintainable.

26. Main End-to-End Scenario

The recruit should demonstrate the following complete flow:

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
12. Creator creates a new version if changes are required
       ↓
13. Activity is recorded