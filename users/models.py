from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        CREATOR = "creator", "Creator"
        REVIEWER = "reviewer", "Reviewer"

    role = models.CharField(max_length=20, choices=Role.choices)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(role__in=["admin", "creator", "reviewer"]),
                name="user_role_valid",
            ),
        ]

    def save(self, *args, **kwargs):
        if self.is_superuser and not self.role:
            self.role = self.Role.ADMIN
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username
