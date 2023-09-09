// Copyright (c) 2023, 8848Digital LLP and contributors
// For license information, please see license.txt

frappe.ui.form.on('Store Credit Assigned', {
	onload: function(frm) {
		if (frm.doc.__islocal) frm.set_value("total_amount",frm.doc.balance_amount)
	},
	credit_amount(frm) {
		frm.set_value("total_amount", (frm.doc.balance_amount + frm.doc.credit_amount))
	}
});
