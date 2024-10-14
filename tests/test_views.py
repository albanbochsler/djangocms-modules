import re

from django.utils.text import capfirst

from cms.api import add_plugin
from cms.models import Placeholder
from cms.utils.plugins import downcast_plugins
from cms.utils.urlutils import add_url_parameters, admin_reverse

from djangocms_modules.cms_plugins import Module
from djangocms_modules.models import ModulePlugin

from .base import BaseModulesPluginTestCase


class ModuleCreatePluginViewsTestCase(BaseModulesPluginTestCase):
    def test_module_add_plugin(self):
        plugin = add_plugin(
            placeholder=self.placeholder,
            plugin_type=Module,
            language=self.DEFAULT_LANGUAGE,
            module_name='test plugin',
            module_category=self.category,
        )
        plugin.full_clean()  # should not raise an error

        self.assertEqual(plugin.plugin_type, "Module")

    def test_create_module_view_get_no_data(self):
        with self.login_user_context(self.superuser):
            response = self.client.get(self.CREATE_MODULE_ENDPOINT)

        self.assertEqual(response.status_code, 400)

    def test_create_module_view_non_staff_denied_access(self):
        response = self.client.get(self.CREATE_MODULE_ENDPOINT)

        self.assertEqual(response.status_code, 403)

    def test_create_module_view_get_provide_form_plugin_is_not_allowed(self):
        plugin = self._add_plugin()

        with self.login_user_context(self.superuser):
            response = self.client.get(self.CREATE_MODULE_ENDPOINT, data={
                'plugin': plugin.pk,
                'language': self.DEFAULT_LANGUAGE,
            })

        self.assertEqual(response.status_code, 400)

    def test_create_module_view_get_show_form_placeholder(self):
        with self.login_user_context(self.superuser):
            response = self.client.get(self.CREATE_MODULE_ENDPOINT, data={
                'placeholder': self.placeholder.pk,
                'language': self.DEFAULT_LANGUAGE,
            })
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.context['form'].initial['placeholder'],
                self.placeholder,
            )

    def test_create_module_view_post_plugin(self):
        plugin = self._add_plugin()

        with self.login_user_context(self.superuser):
            response = self.client.post(self.CREATE_MODULE_ENDPOINT, data={
                'plugin': plugin.pk,
                'category': self.category.pk,
                'language': self.DEFAULT_LANGUAGE,
                'name': 'test module',
            })
            self.assertEqual(response.status_code, 200)

        module_plugins = self.placeholder.get_plugins()

        # Source plugin is kept in original placeholder
        self.assertIn(
            plugin,
            downcast_plugins(self.placeholder.get_plugins()),
        )

        self.assertEqual(module_plugins.count(), 1)
        _plugin = module_plugins[0]
        self.assertEqual(_plugin.plugin_type, plugin.plugin_type)
        self.assertEqual(
            _plugin.get_bound_plugin().module_name,
            plugin.module_name,
        )
        self.assertEqual(
            _plugin.get_bound_plugin().module_category,
            plugin.module_category,
        )

    def test_create_module_view_post_plugin_replace(self):
        plugin = self._add_plugin()

        with self.login_user_context(self.superuser):
            response = self.client.post(self.CREATE_MODULE_ENDPOINT, data={
                'plugin': plugin.pk,
                'category': self.category.pk,
                'name': 'new test module',
                'language': self.DEFAULT_LANGUAGE,
            })

        self.assertEqual(response.status_code, 200)

        plugins = self.placeholder.get_plugins()

        self.assertEqual(plugins.count(), 1)
        self.assertEqual(plugins[0].plugin_type, plugin.plugin_type)
        self.assertEqual(
            plugins[0].get_bound_plugin().module_name,
            plugin.module_name,
        )

    def test_create_module_view_name(self):
        test_plugin = self._test_plugin()

        with self.login_user_context(self.superuser):
            response = self.client.post(self.CREATE_MODULE_ENDPOINT, data={
                'plugin': test_plugin.pk,
                'category': self.category.pk,
                'name': 'test new module',
                'language': self.DEFAULT_LANGUAGE,
            })

        self.assertEqual(response.status_code, 200)

        module_plugin = ModulePlugin.objects.last()
        self.assertEqual(module_plugin.module_name, 'test new module')

    def test_create_module_view_post_no_plugin_or_placeholder(self):
        with self.login_user_context(self.superuser):
            response = self.client.post(self.CREATE_MODULE_ENDPOINT, data={
                'category': self.category.pk,
                'name': 'test module',
                'language': self.DEFAULT_LANGUAGE,
            })
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.context['form'].is_valid())

    def test_create_module_view_post_both_plugin_and_placeholder(self):
        plugin = self._add_plugin()

        with self.login_user_context(self.superuser):
            response = self.client.post(self.CREATE_MODULE_ENDPOINT, data={
                'plugin': plugin.pk,
                'placeholder': self.placeholder.pk,
                'category': self.category.pk,
                'name': 'test module',
                'language': self.DEFAULT_LANGUAGE,
            })
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.context['form'].is_valid())

    def test_create_module_view_post_empty_placeholder(self):
        placeholder = Placeholder(slot='empty')
        placeholder.save()

        with self.login_user_context(self.superuser):
            response = self.client.post(self.CREATE_MODULE_ENDPOINT, data={
                'placeholder': placeholder.pk,
                'category': self.category.pk,
                'name': 'test module',
                'language': self.DEFAULT_LANGUAGE,
            })
            self.assertEqual(response.status_code, 400)
            self.assertEqual(
                response.content.decode(),
                'Plugins are required to create a module',
            )

    def test_create_module_view_post_placeholder(self):
        plugin = self._add_plugin()

        with self.login_user_context(self.superuser):
            response = self.client.post(self.CREATE_MODULE_ENDPOINT, data={
                'placeholder': self.placeholder.pk,
                'category': self.category.pk,
                'name': 'test module',
                'language': self.DEFAULT_LANGUAGE,
            })
            self.assertEqual(response.status_code, 200)

        # Source plugins are kept in original placeholder
        plugins = self.placeholder.get_plugins()
        self.assertEqual(plugins.count(), 1)
        plugin_in_placeholder = plugins[0].get_bound_plugin()
        self.assertEqual(plugin, plugin_in_placeholder)

        module_plugin = ModulePlugin.objects.last()

        source_plugins = self.placeholder.get_plugins()
        module_plugins = module_plugin.placeholder.get_plugins()

        self.assertEqual(module_plugins.count(), source_plugins.count())
        for source, target in zip(source_plugins, module_plugins):
            self.assertEqual(source.plugin_type, target.plugin_type)
            self.assertEqual(
                source.get_bound_plugin().body,
                target.get_bound_plugin().body,
            )

    def test_create_module_view_post_placeholder_replace(self):
        plugin = self._add_plugin()

        placeholder = self.placeholder
        placeholder.get_plugins().delete()
        text_plugin = add_plugin(
            placeholder,
            'TextPlugin',
            language='en',
            body='test 2',
        )

        with self.login_user_context(self.superuser):
            response = self.client.post(self.CREATE_MODULE_ENDPOINT, data={
                'placeholder': placeholder.pk,
                'category': self.category.pk,
                'name': 'test module',
                'language': self.DEFAULT_LANGUAGE,
                'replace': True,
            })
            self.assertEqual(response.status_code, 200)

        module_plugin = ModulePlugin.objects.last()
        module_plugins = module_plugin.placeholder.get_plugins()

        self.assertEqual(module_plugins.count(), 1)
        self.assertEqual(module_plugins[0].plugin_type, plugin.plugin_type)
        self.assertEqual(
            module_plugins[0].get_bound_plugin().body,
            text_plugin.body,
        )

        placeholder_plugins = placeholder.get_plugins()
        self.assertEqual(placeholder_plugins.count(), 1)

        self.assertEqual(
            placeholder_plugins[0].get_bound_plugin().module,
            module_plugin,
        )


class ModuleAddPluginModalViewsTestCase(BaseModulesPluginTestCase):
    def test_module_is_visible_in_template_to_add_plugin_modal(self):
        plugin = self._add_plugin()

        second_page = self._create_page('second test')
        self._publish(second_page)
        second_placeholder = self._get_placeholders(page=second_page).get(
            slot='content',
        )

        with self.login_user_context(self.superuser):
            response = self.client.get(
                admin_reverse(
                    "cms_placeholder_render_object_structure",
                    args=[second_placeholder.content_type_id, second_placeholder.object_id],
                ),
            )

        self.assertEqual(response.status_code, 200)
        self.assertRegex(
            str(response.content),
            r'<script data-cms id="cms-plugin-child-classes-{placeholder_id}" '
            r'type="text/cms-template">'.format(
                placeholder_id=second_placeholder.pk,
            ),
        )
        self.assertRegex(
            str(response.content),
            r'<div class="cms-submenu-item cms-submenu-item-title">'
            r'<span class="cms-submenu-item-title-module">'
            r'<ins class="cms-modules-icon">Modules:</ins> {category_name}'
            r'</span></div>'.format(
                category_name=capfirst(self.category.name),
            ),
        )
        self.assertRegex(
            str(response.content),
            r'<div class="cms-submenu-item"><a data-rel="add" href="Module" '
            r'data-url="{href_url}">{module_name}</a></div>'.format(
                href_url=re.escape(
                    add_url_parameters(
                        admin_reverse(
                            "cms_add_module",
                            args=[plugin.pk],
                        ),
                    ),
                ),
                module_name=plugin.module_name,
            ),
        )
