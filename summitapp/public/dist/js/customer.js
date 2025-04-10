frappe.ui.form.on('Customer', {
    geolocation: function(frm) {
        if (frm.doc.geolocation) {
            try {
                let geojson = JSON.parse(frm.doc.geolocation);
                let coords = geojson.features[0].geometry.coordinates;

                console.log("LOCATION",frm.doc.geolocation)
                frm.set_value('longitude', coords[0]);
                frm.set_value('latitude', coords[1]);
            } catch (e) {
                frappe.msgprint(__('Invalid Geolocation format'));
                console.error(e);
            }
        }
    }
});
