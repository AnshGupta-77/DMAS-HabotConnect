from django.http import FileResponse
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError

from users.models import User

from .models import ActivityLog, Document
from .permissions import DocumentObjectPermission
from .serializers import DocumentSerializer
from .services import log_activity


class DocumentViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = DocumentSerializer
    permission_classes = [DocumentObjectPermission]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        qs = Document.objects.select_related("category", "created_by")
        if user.role == User.Role.ADMIN:
            return qs
        if user.role == User.Role.CREATOR:
            return qs.filter(created_by=user)
        return qs.exclude(status=Document.Status.DRAFT)

    def perform_create(self, serializer):
        document = serializer.save(created_by=self.request.user, status=Document.Status.DRAFT)
        document.versions.create(
            version_number=1, file=document.file, created_by=self.request.user
        )
        log_activity(
            document=document,
            user=self.request.user,
            action=ActivityLog.Action.CREATED,
            description=f"Document '{document.title}' created.",
        )

    def perform_update(self, serializer):
        instance = self.get_object()
        if instance.status not in (Document.Status.DRAFT, Document.Status.CHANGES_REQUESTED):
            raise PermissionDenied("Document cannot be edited in its current status.")
        document = serializer.save()
        log_activity(
            document=document,
            user=self.request.user,
            action=ActivityLog.Action.UPDATED,
            description=f"Document '{document.title}' updated.",
        )

    def perform_destroy(self, instance):
        user = self.request.user
        if user.role != User.Role.ADMIN and instance.status != Document.Status.DRAFT:
            raise PermissionDenied("Only draft documents can be deleted.")
        title, doc_id = instance.title, instance.id
        instance.file.delete(save=False)
        for version in instance.versions.all():
            version.file.delete(save=False)
        instance.delete()
        log_activity(
            document=None,
            user=user,
            action=ActivityLog.Action.DELETED,
            description=f"Document #{doc_id} '{title}' deleted.",
        )

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        document = self.get_object()
        if not document.file:
            raise ValidationError("No file available for this document.")
        return FileResponse(
            document.file.open("rb"), as_attachment=True, filename=document.file.name.rsplit("/", 1)[-1]
        )
