import frappe
from summitapp.utils import error_response


def get_sales_order_details(kwargs):
	if not kwargs.get('order_id'):
		return "Invalid Order Id"
	try:
		doc = frappe.get_doc("Sales Order", kwargs.get("order_id"))
		sales_invoice = frappe.get_all("Sales Invoice", {'sales_order': doc.name}, "*")
		tax = 0
		shipping = 0
		for row in doc.get("taxes", []):
			if "Tax" in row.description:
				tax += row.get("tax_amount",0)
			elif row.description == doc.shipping_rule:
				shipping += row.get("tax_amount",0)
		actionfield = {
			"id": doc.name,
			"affiliation": None,
			"revenue": doc.rounded_total or doc.grand_total,
			"tax": tax,
			"shipping": shipping,
			"coupon": doc.get("coupon_code"),
			"print_url": get_sales_invoice_print_url(sales_invoice)
		}
		products = []
		for row in doc.items:
			category = frappe.db.get_value("Item", row.item_code, "category")
			item = {
				"name": row.item_name,
				"id": row.item_code,
				"price": row.rate,
				"brand": row.brand,
				"category": category,
				"variant": None,
				"quantity": row.qty,
				"coupon": doc.get("coupon_code")
			}
			products.append(item)

		res = {"ecommerce": {
			"purchase": {
				"actionField": actionfield,
				"products": products
				}
		}}
		return res
	except Exception as e:
		frappe.logger('utils').exception(e)
		return error_response("Something went wrong")
	


def get_pdf_link(voucher_type, voucher_no, print_format ="GST Tax Invoice"):
	if print_format:
		return f"{frappe.utils.get_url()}/api/method/frappe.utils.print_format.download_pdf?doctype={voucher_type}&name={voucher_no}&format={print_format}&no_letterhead=1&letterhead=No Letterhead&lang=en"
	return "#"		

def get_sales_invoice_print_url(sales_invoice):
    if sales_invoice:
        return get_pdf_link("Sales Invoice", sales_invoice[0].name)
    else:
        return "#"    