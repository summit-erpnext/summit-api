// Copyright (c) 2025, 8848 Digital LLP and contributors
// For license information, please see license.txt

frappe.ui.form.on("Item Field Details", {
	refresh(frm) {
        frm.trigger("get_item_field_details");
	},
    get_item_field_details(frm) {
        frappe.call({
            method: "summitapp.summitapp.doctype.item_field_details.api.get_item_field_details",
            callback: function(r) {
                if(r.message) {
                    const  field_labels_list = r.message;
                    frm.set_df_property('label', 'options', field_labels_list);
                    frm.refresh_field('label');
                }
            }
        });
    },
});
