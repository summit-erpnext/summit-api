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



def get_translation(key, language):
	translation = frappe.get_all(
		"Translation", filters={"source_text": key, "language": language}, fields=["translated_text"]
	)
	return translation[0]["translated_text"] if translation else key


def translate_keys(data, user_language):
	print("444",data)
	translation_exceptions = ["slug"]
	if isinstance(data, dict):
		translated_data = {}
		for key, value in data.items():
			if key in translation_exceptions:
				# Keep 'slug' as it is without translation
				translated_data[key] = value
			else:
				translated_key = get_translation(key, user_language)
				if value is None:
					value = ""
				translated_data[translated_key] = translate_keys(value, user_language)
		return translated_data
	elif isinstance(data, list):
		return [translate_keys(item, user_language) for item in data]
	else:
		return get_translation(data, user_language)