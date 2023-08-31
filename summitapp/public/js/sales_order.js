frappe.ui.form.on('Sales Order', {
	refresh(frm) {
        if (frm.doc.sales_order_confirmation_created){
            frm.remove_custom_button('Seller Order Confirmation', 'Create');
        }
        else{
            if(frm.doc.docstatus ==1){
                cur_frm.add_custom_button(__('Seller Order Confirmation'), () => frm.trigger('make_seller_order_confirmation')
                ,__('Create'));

            }
           
        }
    },
    make_seller_order_confirmation(frm) {
        frappe.call({
            method:"summitapp.summitapp.doc_events.sales_order.make_seller_order_confirmation",
            args:{'doc':frm.doc.name
            },
        callback: function(r) {
            frappe.msgprint(__("Seller Order Confirmation Created"));
                }
            
        })
    }
})