#!/usr/bin/env python
HELPER_SETTINGS = {
    'INSTALLED_APPS': [
        'djangocms_versioning',
        'djangocms_text',
    ],
    'TEMPLATE_DIRS': [
        'djangocms_modules/templates',
    ],
    'CMS_LANGUAGES': {
        1: [{
            'code': 'en',
            'name': 'English',
        }]
    },
    'LANGUAGE_CODE': 'en',
    'ALLOWED_HOSTS': ['localhost'],
    'CMS_CONFIRM_VERSION4': True,
}


def run():
    from app_helper import runner
    runner.cms('djangocms_modules')


if __name__ == '__main__':
    run()
