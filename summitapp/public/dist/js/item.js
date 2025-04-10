frappe.ui.form.on("Item Images", {
    upload_image: function (frm, cdt, cdn) {
        var row = frappe.get_doc(cdt, cdn);
        var current_date_time = frappe.datetime.now_datetime();
        row.created_on = current_date_time;
        frm.refresh_field("item_images");
    },
});