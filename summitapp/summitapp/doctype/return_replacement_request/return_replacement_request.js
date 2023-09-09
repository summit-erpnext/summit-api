// Copyright (c) 2022, 8848Digital LLP and contributors
// For license information, please see license.txt

frappe.ui.form.on('Return Replacement Request', {
	setup: function(frm) {
		frm.set_query("new_invoice", function() {
			return {
				filters: {
					"customer": frm.doc.customer
				}
			}
		})
	}
});
