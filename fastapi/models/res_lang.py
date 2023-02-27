# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import defaultdict

from accept_language import parse_accept_language

from odoo import api, models, tools


class ResLang(models.Model):
    _inherit = "res.lang"

    @api.model
    @tools.ormcache("accept_language")
    def _get_lang_from_accept_language(self, accept_language):
        """Get the language from the Accept-Language header.

        :param accept_language: The Accept-Language header.
        :return: The language code.
        """
        if not accept_language:
            return
        parsed_accepted_langs = parse_accept_language(accept_language)
        installed_locale_langs = set()
        installed_locale_by_lang = defaultdict(list)
        for lang_code, _name in self.get_installed():
            installed_locale_langs.add(lang_code)
            installed_locale_by_lang[lang_code.split("_")[0]].append(lang_code)

        # parsed_acccepted_langs is sorted by priority (higher first)
        for lang in parsed_accepted_langs:
            # we first check if a locale (en_GB) is available into the list of
            # available locales into Odoo
            locale = None
            if lang.locale in installed_locale_langs:
                locale = lang.locale
            # if no locale language is installed, we look for an available
            # locale for the given language (en). We return the first one
            # found for this language.
            else:
                locales = installed_locale_by_lang.get(lang.language)
                if locales:
                    locale = locales[0]
            if locale:
                return locale
