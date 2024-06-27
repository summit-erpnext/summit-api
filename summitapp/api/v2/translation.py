import frappe
from frappe import _

def get_languages(kwargs):
    get_language_list = frappe.get_list('Language', filters={'enabled': 1}, fields=['language_name','language_code'])
    return get_language_list


def get_translation_text(kwargs):
    language_code = kwargs.get("language_code")
    translation_text_parent = frappe.get_value('Translation Text', {'language_code': language_code})
    if translation_text_parent:
        translatable_fields = frappe.db.get_all(
            'Translatable Fields',
            filters={'parent': translation_text_parent},
            fields=['source_text', 'translated_text']
        )
        translation_dict = {field['source_text']: field['translated_text'] for field in translatable_fields}
        return translation_dict
    else:
        return {"No Translation Text available for selected Language"}

def translate_result(result):
    translated_result = []
    for item in result:
        translated_item = {}
        for fieldname, value in item.items():
            translated_item[fieldname] = _(value)
        translated_result.append(translated_item)
    return translated_result




