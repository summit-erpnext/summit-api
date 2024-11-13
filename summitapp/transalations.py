import frappe

def create_translations():
    translations = [
        {"source": "Tag", "translated": "Featured Collection"},
    ]
    for translation in translations:
        create_translation_if_not_exists(translation["source"], translation["translated"])

def create_translation_if_not_exists(source_text, translated_text):
    if not frappe.db.exists("Translation", {"source_text": source_text}):
        translation_doc = frappe.new_doc("Translation")
        translation_doc.source_text = source_text
        translation_doc.translated_text = translated_text
        translation_doc.save(ignore_permissions=True)


