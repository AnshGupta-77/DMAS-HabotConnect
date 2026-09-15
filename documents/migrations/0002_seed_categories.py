from django.db import migrations

CATEGORIES = ["HR", "Finance", "Technical", "Legal", "General"]


def seed_categories(apps, schema_editor):
    Category = apps.get_model("documents", "Category")
    for name in CATEGORIES:
        Category.objects.get_or_create(name=name)


def remove_categories(apps, schema_editor):
    Category = apps.get_model("documents", "Category")
    Category.objects.filter(name__in=CATEGORIES).delete()


class Migration(migrations.Migration):
    dependencies = [("documents", "0001_initial")]

    operations = [migrations.RunPython(seed_categories, remove_categories)]
