import django_filters

from .models import Document


class DocumentFilterSet(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=Document.Status.choices)
    category = django_filters.CharFilter(field_name="category__name", lookup_expr="iexact")
    created_by = django_filters.NumberFilter(field_name="created_by_id")

    class Meta:
        model = Document
        fields = ["status", "category", "created_by"]
