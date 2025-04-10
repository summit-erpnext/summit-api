frappe.ui.form.on("Customer", {

	fetch_geolocation: (frm) => {
		hrms.fetch_geolocation(frm);
	},
});