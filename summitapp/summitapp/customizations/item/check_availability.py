import frappe
from summitapp.utils import success_response, error_response
from summitapp.api.v2.utils import get_stock_info
from frappe.utils import flt, today, add_days


def check_product_availability(kwargs):
    try:
        item_code = kwargs.get("item_code")
        if not item_code:
            return error_response("item_code missing")

        req_qty = flt(kwargs.get("qty", 1))
        
        stock_qty = flt(get_stock_info(item_code, "stock_qty", with_future_stock=False))

        qty = min(req_qty, stock_qty)

        template_item_code, lead_days = frappe.db.get_value(
            "Item", item_code, ["variant_of", "lead_time_days"])

        warehouse = frappe.db.get_value(
            "Item", {"item_code": item_code}, "website_warehouse")
        
        if not warehouse and template_item_code and template_item_code != item_code:
            warehouse = frappe.db.get_value(
                "Item", {"item_code": template_item_code}, "website_warehouse")

        future_stock = frappe.get_list("Item Future Availability", {
            'item': item_code,
            'date': [">", frappe.utils.today()],
            "quantity": [">", 0]
        }, "warehouse, date, quantity", order_by="date", ignore_permissions=True)
    
        res = []
        data = {
            "warehouse": warehouse,
            "qty": qty,
            "date": today(),
            "incoming_qty": 0,
            "incoming_date": ''
        }
    
        if req_qty <= stock_qty:
            return success_response(data=[data])

        req_qty -= stock_qty

        
        for row in future_stock:
            if req_qty <= 0:
                break

            qty = min(req_qty, row.get("quantity"))
            req_qty -= qty

            if row.get("warehouse") == data["warehouse"] and not data["incoming_qty"]:
                data.update({"incoming_qty": qty, "incoming_date": row.get("date")})
            else:
                res.append({
                    "warehouse": row.get("warehouse"),
                    "incoming_qty": qty,
                    "incoming_date": row.get("date")
                })
            res = [data] + res
    
            if req_qty > 0:
                res[-1].update({
                    "additional_qty": req_qty,
                    "available_on": add_days(row.get("date"), lead_days)  
                })
            return success_response(data=res)
        return success_response(data = "Data Not Found" )
    except Exception as e:
        frappe.logger('product').exception(e)
        return error_response(e)



def get_web_item_future_stock(item_code, item_warehouse_field, warehouse=None):
	in_stock, stock_qty = 0, ""
	template_item_code, is_stock_item = frappe.db.get_value(
		"Item", item_code, ["variant_of", "is_stock_item"]
	)
	if not warehouse:
		warehouse = frappe.db.get_value(
			"Item", {"item_code": item_code}, item_warehouse_field)

	if not warehouse and template_item_code and template_item_code != item_code:
		warehouse = frappe.db.get_value(
			"Item", {
				"item_code": template_item_code}, item_warehouse_field
		)
	if warehouse:
		stock_qty = frappe.db.sql(
			"""
			select sum(quantity)
			from `tabItem Future Availability`
			where date >= CURDATE() and item=%s and warehouse=%s""",
			(item_code, warehouse),
		)

		if stock_qty:
			return stock_qty[0][0]