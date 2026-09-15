from django.conf import settings
from django.db import models

from .storage import document_upload_path, version_upload_path
from .validators import validate_document_file


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Document(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"
        UNDER_REVIEW = "under_review", "Under Review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        CHANGES_REQUESTED = "changes_requested", "Changes Requested"

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="documents")
    file = models.FileField(upload_to=document_upload_path, validators=[validate_document_file])
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="documents"
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    current_version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    status__in=[
                        "draft",
                        "submitted",
                        "under_review",
                        "approved",
                        "rejected",
                        "changes_requested",
                    ]
                ),
                name="document_status_valid",
            ),
        ]
        indexes = [
            models.Index(fields=["created_by", "status"]),
            models.Index(fields=["status"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return self.title


class DocumentVersion(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="versions")
    version_number = models.PositiveIntegerField()
    file = models.FileField(upload_to=version_upload_path, validators=[validate_document_file])
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    comment = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["document", "version_number"], name="unique_document_version_number"
            ),
        ]
        ordering = ["version_number"]

    def __str__(self):
        return f"{self.document_id} v{self.version_number}"


class Comment(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment({self.document_id}, {self.user_id})"


class ActivityLog(models.Model):
    class Action(models.TextChoices):
        CREATED = "document_created", "Document Created"
        UPDATED = "document_updated", "Document Updated"
        SUBMITTED = "document_submitted", "Document Submitted"
        REVIEWED = "document_reviewed", "Document Reviewed"
        APPROVED = "document_approved", "Document Approved"
        REJECTED = "document_rejected", "Document Rejected"
        CHANGES_REQUESTED = "changes_requested", "Changes Requested"
        COMMENT_ADDED = "comment_added", "Comment Added"
        VERSION_CREATED = "version_created", "Version Created"
        DELETED = "document_deleted", "Document Deleted"

    document = models.ForeignKey(
        Document, on_delete=models.SET_NULL, null=True, related_name="activity_logs"
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=30, choices=Action.choices)
    description = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["document", "-created_at"])]

    def __str__(self):
        return f"{self.action} ({self.document_id})"
