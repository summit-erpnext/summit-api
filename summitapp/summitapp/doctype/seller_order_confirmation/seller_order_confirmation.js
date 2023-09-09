// Copyright (c) 2022, 8848Digital LLP and contributors
// For license information, please see license.txt

frappe.ui.form.on('Seller Order Confirmation', {
	refresh: function(frm) {
		if(frm.doc.commission_sales_invoice_created){
			console.log("wetw")
			frm.remove_custom_button('Create Commission Sales Invoice', 'Create');
		}
		else{
			if (frm.doc.workflow_state == "Approved"){
				frm.add_custom_button('Create Commission Sales Invoice', function() {
						frm.trigger('make_sales_invoice')
						frappe.msgprint(__("Commission Sales Invoice Created"));
				 },__('Create'));
			 }
		}
		
	},
	make_sales_invoice(frm) {
        frappe.call({
            method:"summitapp.summitapp.doctype.seller_order_confirmation.seller_order_confirmation.make_sales_invoice",
            args:{'doc':frm.doc.name
            },
        	callback: function(r) {
            	frappe.msgprint(__("Sales Invoice Created"));
            }
         })
    }
});