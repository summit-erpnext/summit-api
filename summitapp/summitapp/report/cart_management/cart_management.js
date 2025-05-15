// Copyright (c) 2025, 8848 Digital LLP and contributors
// For license information, please see license.txt

frappe.query_reports["Cart Management"] = {
    "filters": [
        {
            "fieldname": "customer",
            "label": __("Customer"),
            "fieldtype": "Link",
            "options": "Customer",
            "default": ""
        },
        {
            "fieldname": "custom_party_name",
            "label": __("Party Name"),
            "fieldtype": "Link",
            "options": "Customer",
            "default": ""
        },
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
            "reqd": 1
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1
        },
        {
            "fieldname": "company",
            "label": __("Company"),
            "fieldtype": "Link",
            "options": "Company",
            "default": frappe.defaults.get_user_default("Company")
        },
        {
			"fieldname": "status",
			"label": __("Status"),
			"fieldtype": "Select",
			"options": "\nDraft\nOpen\nReplied\nPartially Ordered\nOrdered\nLost\nCancelled\nExpired",
			"default": ""
		}


    ]
};
