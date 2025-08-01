import frappe


def resync_cart(session):
    """
    Resync User Session Cart With Logged In User Cart
    Delete Session Cart After Transferring Items To User Cart.
    """
    try:
        # Check if a Quotation with the given session ID and status "Draft" exists
        name = frappe.db.exists('Quotation', {'session_id': session, "status": "Draft"})
        
        if name:
            data = {"owner": frappe.session.user}
            
            customer = frappe.db.get_value("Customer", {"email": frappe.session.user}, "name")
            if customer:
                data["party_name"] = customer

            # Check if an existing Quotation with status "Draft" is owned by the logged-in user
            existing_doc = frappe.db.exists("Quotation", {"owner": frappe.session.user, "status": "Draft"})
            
            if existing_doc:
                # Transfer items from the session's Quotation to the user's Quotation
                items = frappe.db.sql(f"select item_code, qty from `tabQuotation Item` where parent = '{name}'", as_dict=True)
                doc = frappe.get_doc("Quotation", existing_doc)

                for item in items:
                    quotation_items = [qi for qi in doc.get("items") if qi.item_code == item.item_code]
                    if not quotation_items:
                        doc.append("items", {
                            "doctype": "Quotation Item",
                            "item_code": item.item_code,
                            "qty": item.qty
                        })
                    else:
                        quotation_items[0].qty = item.qty

                if customer and not doc.party_name:
                    doc.party_name = customer

                doc.flags.ignore_permissions = True
                doc.save()

                # Delete the session's Quotation after transferring items
                frappe.delete_doc('Quotation', name, ignore_permissions=True)
            else:
                # Set the owner and party_name for the session's Quotation if it's not already owned by the user
                frappe.db.set_value("Quotation", name, data)
                frappe.db.commit()

            # Get the guest user's email associated with the session and delete the guest user
            guest_user = frappe.db.get_list("Access Token", filters={"token": session}, fields=['email'])
            if guest_user:
                frappe.delete_doc('User', guest_user[0].email, ignore_permissions=True, force=True)

            return "success"
        else:
            return {"msg": "no quotation Found", "session": session, "f_session": frappe.session}
    except Exception as e:
        frappe.logger('utils').exception(e)
        return None  # Return a consistent type in case of an error

