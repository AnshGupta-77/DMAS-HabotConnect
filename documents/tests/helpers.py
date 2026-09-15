from django.core.files.uploadedfile import SimpleUploadedFile

from documents.models import Category
from users.models import User

PDF_BYTES = b"%PDF-1.4\n%%EOF"


def make_user(username, role, password="StrongPass123"):
    return User.objects.create_user(username=username, email=f"{username}@example.com", password=password, role=role)


def make_category(name="HR"):
    category, _ = Category.objects.get_or_create(name=name)
    return category


def pdf_file(name="doc.pdf", content=PDF_BYTES):
    return SimpleUploadedFile(name, content, content_type="application/pdf")


def auth_client(client, user):
    from rest_framework_simplejwt.tokens import RefreshToken

    token = RefreshToken.for_user(user).access_token
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client
