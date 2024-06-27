// // your_doctype.js
// frappe.ui.form.on('Encryption', {
//     onload: function(frm) {
//         // Use frappe.utils.password to decrypt sensitive data
//         frm.doc.email = frappe.utils.password.get_decrypted_password('Encryption', frm.doc.name, fieldname='email');
//         frm.doc.phone = frappe.utils.password.get_decrypted_password('Encryption', frm.doc.name, fieldname='phone');
//         frm.refresh_field('email');
//         frm.refresh_field('phone');
//     }
// });
