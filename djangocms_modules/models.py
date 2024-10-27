from django.db import models
from django.dispatch import receiver
from django.urls import Resolver404, resolve
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from cms import operations
from cms.models import CMSPlugin, Placeholder
from cms.models.fields import PlaceholderRelationField
from cms.signals import pre_placeholder_operation
from cms.utils.plugins import get_bound_plugins


@receiver(pre_placeholder_operation)
def sync_module_plugin(sender, **kwargs):
    """
    Updates the created placeholder operation record,
    based on the configured post operation handlers.
    """
    operation_type = kwargs.pop('operation')
    affected_operations = (operations.MOVE_PLUGIN, operations.PASTE_PLUGIN)

    if operation_type not in affected_operations:
        return

    try:
        match = resolve(kwargs['origin'])
    except Resolver404:
        match = None

    is_in_modules = match and match.url_name == 'cms_modules_list'

    if not is_in_modules:
        return

    plugin = kwargs['plugin']
    placeholder = kwargs.get('target_placeholder')
    needs_sync = (
        plugin.plugin_type
        == 'Module'
        and placeholder.pk
        != plugin.module_category.modules_id
    )

    if needs_sync:
        # User has moved module to another category placeholder
        # or pasted a copied module plugin.
        new_category = Category.objects.get(modules=placeholder)
        (ModulePlugin
         .objects
         .filter(path__startswith=plugin.path, depth__gte=plugin.depth)
         .update(module_category=new_category))


class Category(models.Model):
    PLACEHOLDER_SLOT_NAME = "module-category"

    name = models.CharField(
        verbose_name=_('Name'),
        max_length=120,
        unique=True,
    )
    placeholders = PlaceholderRelationField()

    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')

    def __str__(self):
        return self.name

    @cached_property
    def modules_placeholder(self):
        from cms.utils.placeholder import get_placeholder_from_slot

        return get_placeholder_from_slot(self.placeholders, self.PLACEHOLDER_SLOT_NAME)

    def get_non_empty_modules(self):
        unbound_plugins = (
            self
            .modules_placeholder
            .get_plugins()  # TODO: filter by current language?
            .filter(parent__isnull=True)
        )
        return get_bound_plugins(unbound_plugins)

    def get_template(self):
        return "djangocms_modules/modules_structure_mode.html"

    @cached_property
    def app_context(self):
        return {
            'modules_page': True,
        }

class ModulesPlaceholder(Placeholder):

    class Meta:
        proxy = True

    def _get_attached_model(self):
        return Category

    def _get_attached_models(self):
        return self._get_attached_model()

    def _get_attached_objects(self):
        return self._get_attached_model().objects.filter(modules=self.pk)

    @cached_property
    def category(self):
        return self._get_attached_model().objects.get(modules=self.pk)

    def get_label(self):
        return self.category.name


class ModulePlugin(CMSPlugin):
    module_name = models.CharField(
        verbose_name=_('Name'),
        max_length=120,
    )
    module_category = models.ForeignKey(
        to=Category,
        verbose_name=_('Category'),
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.module_name

    def update(self, refresh=False, **fields):
        ModulePlugin.objects.filter(pk=self.pk).update(**fields)
        if refresh:
            return self.reload()
        return

    def get_unbound_plugins(self):
        return self.cmsplugin_set.filter(language=self.language).order_by("position")
