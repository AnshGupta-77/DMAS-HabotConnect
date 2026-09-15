from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from users.models import User

from .filters import DocumentFilterSet
from .models import ActivityLog, Document
from .permissions import DocumentObjectPermission
from .serializers import ActivityLogSerializer, CommentSerializer, DocumentSerializer
from .services import apply_transition, log_activity

WORKFLOW_ACTIONS = {"submit", "review", "approve", "reject", "request_changes"}
NESTED_READ_ACTIONS = {"comments", "activity"}


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
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DocumentFilterSet
    search_fields = ["title", "category__name", "status", "created_by__username"]
    ordering_fields = ["created_at", "updated_at", "title", "status"]
    ordering = ["-created_at"]

    def get_permissions(self):
        if self.action in WORKFLOW_ACTIONS or self.action in NESTED_READ_ACTIONS:
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

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

    def _run_transition(self, request, action_name, comment_field=None):
        document = self.get_object()
        comment_text = request.data.get(comment_field, "") if comment_field else ""
        document = apply_transition(
            action_name=action_name, document_id=document.id, user=request.user, comment_text=comment_text
        )
        return Response(DocumentSerializer(document, context={"request": request}).data)

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        return self._run_transition(request, "submit")

    @action(detail=True, methods=["post"])
    def review(self, request, pk=None):
        return self._run_transition(request, "review")

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        return self._run_transition(request, "approve")

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        return self._run_transition(request, "reject", comment_field="reason")

    @action(detail=True, methods=["post"], url_path="request-changes")
    def request_changes(self, request, pk=None):
        return self._run_transition(request, "request_changes", comment_field="comment")

    @action(detail=True, methods=["get", "post"])
    def comments(self, request, pk=None):
        document = self.get_object()
        if request.method == "POST":
            serializer = CommentSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(document=document, user=request.user)
            log_activity(
                document=document,
                user=request.user,
                action=ActivityLog.Action.COMMENT_ADDED,
                description="Comment added.",
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        queryset = document.comments.select_related("user")
        page = self.paginate_queryset(queryset)
        serializer = CommentSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=["get"])
    def activity(self, request, pk=None):
        document = self.get_object()
        queryset = document.activity_logs.select_related("user")
        page = self.paginate_queryset(queryset)
        serializer = ActivityLogSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)
