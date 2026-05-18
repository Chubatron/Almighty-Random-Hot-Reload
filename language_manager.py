import json
import os
from kivy.event import EventDispatcher
from kivy.properties import StringProperty
from kivy.storage.jsonstore import JsonStore


class LanguageManager(EventDispatcher):
    current_lang = StringProperty('ru')

    __events__ = ('on_language_changed',)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.translations = {}
        self.store = JsonStore('settings.json')

        if self.store.exists('language'):
            saved_lang = self.store.get('language')['code']
        else:
            saved_lang = 'ru'

        self.load_language(saved_lang)

    def load_language(self, lang_code):
        self.current_lang = lang_code
        file_path = os.path.join('locales', f'{lang_code}.json')

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)

            self.store.put('language', code=lang_code)
            self.dispatch('on_language_changed')
            return True

        except FileNotFoundError:
            if lang_code != 'ru':
                return self.load_language('ru')
            return False
        except json.JSONDecodeError:
            return False

    def on_language_changed(self, *args):
        pass

    def _(self, key):
        return self.translations.get(key, key)

    def get_available_languages(self):
        languages = []
        locales_path = 'locales'

        if not os.path.exists(locales_path):
            return languages

        for file in os.listdir(locales_path):
            if file.endswith('.json'):
                lang_code = file.replace('.json', '')

                lang_names = {
                    'en': 'English',
                    'ru': 'Русский',
                    'zh': '中文',
                    'hi': 'हिन्दी',
                    'es': 'Español',
                    'ar': 'العربية',
                    'uk': 'Українська',
                }

                name = lang_names.get(lang_code, lang_code)
                languages.append({'code': lang_code, 'name': name})

        languages.sort(key=lambda x: x['name'])
        return languages

    def is_rtl(self, lang_code=None):
        if lang_code is None:
            lang_code = self.current_lang
        rtl_languages = ['ar']
        return lang_code in rtl_languages