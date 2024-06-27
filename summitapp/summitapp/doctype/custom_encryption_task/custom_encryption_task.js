
frappe.ui.form.on('custom encryption task', {
    before_save: function(frm) {
        if (frm.doc.email && frm.doc.phone_no) {
            frappe.call({
                method: "summitapp.summitapp.doctype.custom_encryption_task.custom_encryption_task.set_encrypted_value",
                args: { doc: frm.doc },
                callback: function(response) {
                    console.log("response",response)
                    frm.set_value("email", response.message[0]);
                    frm.set_value("phone_no", response.message[1]);       
                }
            });
        }
    },
});