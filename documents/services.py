from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError

from notifications.services import notify
from users.models import User

from .models import ActivityLog, Comment, Document

TRANSITIONS = {
    "submit": {
        "from": Document.Status.DRAFT,
        "to": Document.Status.SUBMITTED,
        "roles": (User.Role.CREATOR, User.Role.ADMIN),
        "owner_only": True,
        "action": ActivityLog.Action.SUBMITTED,
    },
    "review": {
        "from": Document.Status.SUBMITTED,
        "to": Document.Status.UNDER_REVIEW,
        "roles": (User.Role.REVIEWER, User.Role.ADMIN),
        "owner_only": False,
        "action": ActivityLog.Action.REVIEWED,
    },
    "approve": {
        "from": Document.Status.UNDER_REVIEW,
        "to": Document.Status.APPROVED,
        "roles": (User.Role.REVIEWER, User.Role.ADMIN),
        "owner_only": False,
        "action": ActivityLog.Action.APPROVED,
    },
    "reject": {
        "from": Document.Status.UNDER_REVIEW,
        "to": Document.Status.REJECTED,
        "roles": (User.Role.REVIEWER, User.Role.ADMIN),
        "owner_only": False,
        "action": ActivityLog.Action.REJECTED,
    },
    "request_changes": {
        "from": Document.Status.UNDER_REVIEW,
        "to": Document.Status.CHANGES_REQUESTED,
        "roles": (User.Role.REVIEWER, User.Role.ADMIN),
        "owner_only": False,
        "action": ActivityLog.Action.CHANGES_REQUESTED,
    },
}


def log_activity(*, document, user, action, description=""):
    return ActivityLog.objects.create(
        document=document, user=user, action=action, description=description
    )


@transaction.atomic
def apply_transition(*, action_name, document_id, user, comment_text=""):
    rule = TRANSITIONS[action_name]
    document = Document.objects.select_for_update().get(id=document_id)

    if user.role not in rule["roles"]:
        raise PermissionDenied("You do not have permission to perform this action.")
    if rule["owner_only"] and document.created_by_id != user.id and user.role != User.Role.ADMIN:
        raise PermissionDenied("You do not have permission to perform this action.")
    if document.status != rule["from"]:
        raise ValidationError(
            f"Cannot {action_name.replace('_', ' ')} a document in status '{document.status}'."
        )

    if action_name == "reject" and not comment_text.strip():
        raise ValidationError({"reason": "A rejection reason is required."})
    if action_name == "request_changes" and not comment_text.strip():
        raise ValidationError({"comment": "A comment explaining the requested changes is required."})

    document.status = rule["to"]
    document.save(update_fields=["status", "updated_at"])

    if comment_text.strip():
        Comment.objects.create(document=document, user=user, comment=comment_text.strip())

    log_activity(document=document, user=user, action=rule["action"])

    if action_name == "submit":
        reviewers = User.objects.filter(role=User.Role.REVIEWER, is_active=True)
        notify(reviewers, "You have a document waiting for review.")
    elif action_name == "approve":
        notify([document.created_by], "Your document has been approved.")
    elif action_name == "reject":
        notify([document.created_by], "Your document has been rejected.")
    elif action_name == "request_changes":
        notify([document.created_by], "Changes have been requested for your document.")

    return document
