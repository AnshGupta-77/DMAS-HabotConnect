from django.conf import settings
from django.core.exceptions import ValidationError

ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "xls", "xlsx", "txt"}

_MAGIC_CHECKS = {
    "pdf": lambda head: head.startswith(b"%PDF-"),
    "doc": lambda head: head.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"),
    "xls": lambda head: head.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"),
    "docx": lambda head: head.startswith(b"PK\x03\x04"),
    "xlsx": lambda head: head.startswith(b"PK\x03\x04"),
}


def validate_document_file(uploaded_file):
    if not uploaded_file:
        raise ValidationError("File is required.")

    name = uploaded_file.name or ""
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"Unsupported file type '.{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}."
        )

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if uploaded_file.size > max_bytes:
        raise ValidationError(f"File exceeds the {settings.MAX_UPLOAD_SIZE_MB}MB limit.")

    head = uploaded_file.read(8)
    uploaded_file.seek(0)

    if ext == "txt":
        _validate_text_file(uploaded_file)
        return

    check = _MAGIC_CHECKS[ext]
    if not check(head):
        raise ValidationError("File content does not match its extension.")


def _validate_text_file(uploaded_file):
    content = uploaded_file.read()
    uploaded_file.seek(0)
    if b"\x00" in content:
        raise ValidationError("File content does not match its extension.")
    try:
        content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValidationError("File content does not match its extension.") from exc
