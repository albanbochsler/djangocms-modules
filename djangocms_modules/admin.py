from django.contrib import admin

from cms.admin.placeholderadmin import PlaceholderAdminMixin, FrontendEditableAdminMixin
from cms.toolbar.utils import get_object_preview_url
from .models import Category


@admin.register(Category)
class CategoryAdmin(FrontendEditableAdminMixin, PlaceholderAdminMixin, admin.ModelAdmin):
    list_display = ['name']

    def view_on_site(self, obj):
        return get_object_preview_url(obj, "de")
