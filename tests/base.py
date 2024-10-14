from django.contrib.auth import get_user_model

from cms.api import add_plugin, create_page, create_title
from cms.test_utils.testcases import CMSTestCase
from cms.utils.urlutils import admin_reverse

from djangocms_text.cms_plugins import TextPlugin

from djangocms_modules.cms_plugins import Module
from djangocms_modules.models import Category


try:
    import djangocms_versioning  # noqa

    DJANGO_CMS4 = True
except ImportError:
    DJANGO_CMS4 = False


User = get_user_model()


class TestFixture:
    DEFAULT_LANGUAGE = 'en'
    superuser: User

    if DJANGO_CMS4:  # CMS V4

        def _get_version(self, page, version_state, language=None):
            language = language or self.DEFAULT_LANGUAGE

            from djangocms_versioning.models import Version

            versions = Version.objects.filter_by_grouper(page).filter(
                state=version_state
            )
            for version in versions:
                if (
                    hasattr(version.content, "language")
                    and version.content.language == language
                ):
                    return version

        def _publish(self, page, language=None):
            from djangocms_versioning.constants import DRAFT

            version = self._get_version(page, DRAFT, language)
            if version is not None:
                version.publish(self.superuser)

        def _unpublish(self, page, language=None):
            from djangocms_versioning.constants import PUBLISHED

            version = self._get_version(page, PUBLISHED, language)
            if version is not None:
                version.unpublish(self.superuser)

        def _create_page(self, title, **kwargs):
            kwargs.setdefault("language", self.DEFAULT_LANGUAGE)
            kwargs.setdefault("template", "page.html")
            kwargs.setdefault("created_by", self.superuser)
            kwargs.setdefault("in_navigation", True)
            kwargs.setdefault("limit_visibility_in_menu", None)
            kwargs.setdefault("menu_title", title)
            return create_page(
                title=title,
                **kwargs
            )

        def _get_placeholders(self, page):
            return page.get_placeholders(self.DEFAULT_LANGUAGE)

    else:  # CMS V3

        def _publish(self, page, language=None):
            page.publish(language)

        def _unpublish(self, page, language=None):
            page.unpublish(language)

        def _create_page(self, title, **kwargs):
            kwargs.setdefault("language", self.DEFAULT_LANGUAGE)
            kwargs.setdefault("template", "page.html")
            kwargs.setdefault("menu_title", title)
            return create_page(
                title=title,
                **kwargs
            )

        def _get_placeholders(self, page):
            return page.get_placeholders()


class BaseModulesPluginTestCase(TestFixture, CMSTestCase):
    CREATE_MODULE_ENDPOINT = admin_reverse('cms_create_module')
    LIST_MODULE_ENDPOINT = admin_reverse('cms_modules_list')

    def setUp(self):
        self.superuser = self.get_superuser()
        self.page = self._create_page('test')
        self._publish(self.page)
        self.placeholder = self._get_placeholders(page=self.page).get(
            slot='content',
        )
        self.category = Category.objects.create(name='test category')

    def _add_plugin(self):
        plugin = add_plugin(
            placeholder=self.placeholder,
            plugin_type=Module,
            language=self.DEFAULT_LANGUAGE,
            module_name='test plugin',
            module_category=self.category,
        )
        return plugin

    def _test_plugin(self):
        plugin = add_plugin(
            placeholder=self.placeholder,
            plugin_type=TextPlugin,
            language=self.DEFAULT_LANGUAGE,
        )
        return plugin

    def _get_draft_page_placeholder(self):
        page_content = create_title(self.DEFAULT_LANGUAGE, 'Draft Page', self.page, created_by=self.superuser)
        return page_content.get_placeholders().get(slot='content')
