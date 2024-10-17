from cms.app_base import CMSAppConfig

from . import models, views


class ModulesConfig(CMSAppConfig):
    cms_enabled = True
    cms_toolbar_enabled_models = [(models.ModulePlugin, views.render_module_plugin)]

