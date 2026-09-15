from django.core.exceptions import ValidationError as DjangoValidationError
from django.urls import reverse
from rest_framework import serializers

from .models import ActivityLog, Comment, Document, DocumentVersion
from .validators import validate_document_file


class DocumentSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    created_by_username = serializers.CharField(source="created_by.username", read_only=True)
    download_url = serializers.SerializerMethodField()
    file = serializers.FileField(write_only=True)

    class Meta:
        model = Document
        fields = [
            "id",
            "title",
            "description",
            "category",
            "category_name",
            "file",
            "download_url",
            "created_by",
            "created_by_username",
            "status",
            "current_version",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["status", "created_by", "current_version", "created_at", "updated_at"]

    def get_download_url(self, obj):
        request = self.context.get("request")
        url = reverse("document-download", kwargs={"pk": obj.pk})
        return request.build_absolute_uri(url) if request else url

    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Title cannot be blank.")
        return value

    def validate_file(self, value):
        try:
            validate_document_file(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        return value

    def update(self, instance, validated_data):
        validated_data.pop("file", None)
        return super().update(instance, validated_data)


class CommentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "document", "user", "username", "comment", "created_at"]
        read_only_fields = ["document", "user", "created_at"]

    def validate_comment(self, value):
        if not value.strip():
            raise serializers.ValidationError("Comment cannot be empty.")
        return value


class DocumentVersionSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source="created_by.username", read_only=True)
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = DocumentVersion
        fields = [
            "id",
            "document",
            "version_number",
            "file",
            "download_url",
            "created_by",
            "created_by_username",
            "comment",
            "created_at",
        ]
        read_only_fields = ["document", "version_number", "created_by", "created_at"]
        extra_kwargs = {"file": {"write_only": True}}

    def get_download_url(self, obj):
        request = self.context.get("request")
        url = reverse(
            "document-version-download", kwargs={"pk": obj.document_id, "version_id": obj.id}
        )
        return request.build_absolute_uri(url) if request else url


class ActivityLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True, default=None)

    class Meta:
        model = ActivityLog
        fields = ["id", "document", "user", "username", "action", "description", "created_at"]
        read_only_fields = fields
