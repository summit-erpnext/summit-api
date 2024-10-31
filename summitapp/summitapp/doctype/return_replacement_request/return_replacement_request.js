// Copyright (c) 2024, 8848 Digital LLP and contributors
// For license information, please see license.txt

frappe.ui.form.on("Return Replacement Request", {
	setup: function(frm) {
		frm.set_query("new_invoice", function() {
			return {
				filters: {
					"customer": frm.doc.customer
				}
			}
		})
	},
	order_id: function(frm){
		if (frm.doc.order_id){
			frm.set_query("product_id", function() {
				return {
					query: "summitapp.summitapp.doctype.return_replacement_request.return_replacement_request.get_items_from_sales",
					filters: {
						"sales_order": frm.doc.order_id
					}
				}
			})
		}
	},
});