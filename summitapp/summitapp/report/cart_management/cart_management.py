# Copyright (c) 2025, 8848 Digital LLP and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": "Quotation ID", "fieldname": "name", "fieldtype": "Link", "options": "Quotation", "width": 200},
        {"label": "Customer", "fieldname": "party_name", "fieldtype": "Link", "options": "Customer", "width": 150},
        {"label": "Customer Name", "fieldname": "customer_name", "fieldtype": "Data", "width": 150},
        {"label": "Party Name", "fieldname": "custom_party_name", "fieldtype": "Link", "options": "Customer","width": 200},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100}
    ]

def get_data(filters):
    conditions = []

    if filters.get("customer"):
        conditions.append("q.party_name = %(customer)s")
    if filters.get("custom_party_name"):
        conditions.append("q.custom_party_name = %(custom_party_name)s")
    if filters.get("from_date"):
        conditions.append("q.transaction_date >= %(from_date)s")
    if filters.get("to_date"):
        conditions.append("q.transaction_date <= %(to_date)s")
    if filters.get("company"):
        conditions.append("q.company = %(company)s")
    if filters.get("status"):
        conditions.append("q.status = %(status)s")

    condition_str = " AND ".join(conditions) or "1=1"

    query = f"""
        SELECT
            q.name,
            q.party_name,
            q.customer_name,
            q.custom_party_name,
            q.status
        FROM
            `tabQuotation` q
        WHERE
            {condition_str}
        ORDER BY
            q.transaction_date DESC
    """

    return frappe.db.sql(query, filters, as_dict=True)
