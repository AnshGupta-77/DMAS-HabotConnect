from django.db.models import Count, Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from documents.models import Document
from users.models import User


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        qs = Document.objects.all()
        if user.role == User.Role.CREATOR:
            qs = qs.filter(created_by=user)
        elif user.role == User.Role.REVIEWER:
            qs = qs.exclude(status=Document.Status.DRAFT)

        counts = qs.aggregate(
            total_documents=Count("id"),
            draft_documents=Count("id", filter=Q(status=Document.Status.DRAFT)),
            submitted_documents=Count("id", filter=Q(status=Document.Status.SUBMITTED)),
            pending_reviews=Count("id", filter=Q(status=Document.Status.UNDER_REVIEW)),
            approved_documents=Count("id", filter=Q(status=Document.Status.APPROVED)),
            rejected_documents=Count("id", filter=Q(status=Document.Status.REJECTED)),
        )
        return Response(counts)
