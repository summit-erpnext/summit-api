import frappe
from frappe import _
import requests
from summitapp.utils import error_response, success_response
from frappe.utils import getdate, now_datetime, add_months
from datetime import datetime
from datetime import timedelta
from frappe.utils.dateutils import get_period, get_dates_from_timegrain
from summitapp.api.v2.utils import get_logged_user

@frappe.whitelist()
def get_dealer_ledger(kwargs):
	frappe.set_user("Administrator")
	try:
		email = None	
		headers = frappe.request.headers
		if not headers or 'Authorization' not in headers:
			return error_response('Please Specify Authorization Token')
		if headers:
			email = get_logged_user()
			if kwargs.get("from_date") and kwargs.get("to_date"):
				start = getdate(kwargs.get("from_date"), "%d-%m-%Y")
				end = getdate(kwargs.get("to_date"), "%d-%m-%Y")
				range = f"{kwargs.get('from_date')} To {kwargs.get('to_date')}"
			else:
				start, end = get_dates(kwargs.get('month'))
				range = kwargs.get('month')
			party = kwargs.get('party')
			if not party:
				party = frappe.db.get_value("Customer", {"email", email})
		report = frappe.get_doc(
			"Report", "General Ledger", ignore_permissions=True)
		custom_filter = {
			"company": kwargs.get('company', frappe.db.get_single_value("Global Defaults", "default_company")),
			"from_date": start, "to_date": end,
			"group_by": "Group by Voucher (Consolidated)", "include_dimensions": 1, "party_type": "Customer",
			"party": [kwargs.get('party')]
		}
		col, data = report.get_data(filters=custom_filter, as_dict=True)
		# first & last row would be opening & closing balances
		first, last = data[0], data[-1]
		due_date_obj = end.replace(day=13)
		due_date= due_date_obj.strftime('%Y-%m-%d')
		general_data = {
			"opening_balance": first.get("balance"),
			"payment_due_date":due_date,
			"credit_opening_balance": first.get('credit'),
			"credit_closing_balance": last.get("credit"),
			"debit_opening_balance": first.get('debit'),
			"debit_closing_balance": last.get("debit"),
			"current_total": last.get("balance")
		}
		sales_data = []
		sno = 1
		opening_blnc = first.get('balance')
		# credit_opening = first.get("credit")
		# debit_opening = first.get("debit")
		for row in data[1:-2]:
			sales = {
				"id": sno,
				"party_name": row.get("party"),
				"posting_date": row.get("posting_date").strftime("%d-%m-%Y"),
				"opening_balance": opening_blnc,
				"closing_balance": row.get("balance"),
				# "credit_opening_balance": credit_opening,
				# "debit_opening_balance": debit_opening,
				"debit_amount": row.get("debit"),
				"credit_amount": row.get("credit"),
				"voucher_type": row.get("voucher_type"),
				"Voucher_number": row.get("voucher_no"),
				"pdf_link": get_si_pdf_link(row.get("voucher_type"), row.get("voucher_no"))
			}
			# opening_blnc = row.get("balance")
			# credit_opening += row.get("credit")
			# debit_opening += row.get("debit")
			sno += 1
			sales_data.append(sales)

		result = {
			'party_name': kwargs.get('party'),
			'range': range,
			'general_data': general_data,
			'sales_data': sales_data
		}
		return success_response(data=result)
	except Exception as e:
		frappe.logger('gl').exception(e)
		return error_response(e)

def get_si_pdf_link(voucher_type, voucher_no):
	if voucher_type != "Sales Invoice":
		return "#"
	return f"{frappe.utils.get_url()}/api/method/frappe.utils.print_format.download_pdf?doctype=Sales%20Invoice&name={voucher_no}&format=Standard%20SI&no_letterhead=0&letterhead=final%20sales%20%20Invoice&settings=%7B%7D&_lang=en"
	# return f"{frappe.utils.get_url()}/api/method/sportnetwork.utils.download_pdf?doctype=Sales%20Invoice&name={voucher_no}&format=Standard%20SI&no_letterhead=0&letterhead=final%20sales%20%20Invoice&settings=%7B%7D&_lang=en"

@frappe.whitelist()
def get_ledger_summary(kwargs):
	frappe.set_user("Administrator")
	try:
		email = None	
		headers = frappe.request.headers
		if not headers or 'Authorization' not in headers:
			return error_response('Please Specify Authorization Token')
		if headers:
			email = get_logged_user()
		party = frappe.db.get_value("Customer", {"email": email})
		report = frappe.get_doc(
			"Report", "Customer Credit Balance", ignore_permissions=True)
		custom_filter = {
			"company": kwargs.get('company', frappe.db.get_single_value("Global Defaults", "default_company")),
			"customer": party
		}
		col, data = report.get_data(filters=custom_filter, as_dict=True)
		general_ledger_report = frappe.get_doc(
			"Report", "General Ledger", ignore_permissions=True)
		current_date = getdate()
		one_month_ago_date = current_date - timedelta(days=current_date.day)
		thirteenth_date_next_month = add_months(current_date, 1).replace(day=13)
		
		ledger_custom_filter = {
			"company": kwargs.get('company', frappe.db.get_single_value("Global Defaults", "default_company")),
			"from_date":one_month_ago_date , "to_date":current_date,
			"group_by": "Group by Voucher (Consolidated)", "include_dimensions": 1, "party_type": "Customer",
			"party":[party]
		}
		ledger_col, ledger_data = general_ledger_report.get_data(filters=ledger_custom_filter, as_dict=True)
		first = ledger_data[0]
		result = {}
		if data:
			data = data[0]
			first_entry = frappe.db.get_value(
				"GL Entry", {"party": party}, 'posting_date', order_by='posting_date asc')
			dates = list(map(get_period, get_dates_from_timegrain(
				getdate(first_entry), now_datetime(), "Monthly")))
			result = {
				"party_name": data.get("customer"),
				"remaining_credit_balance": data.get("credit_balance"),
				"total_credit_amount": data.get("credit_limit"),
				"due_payment_amount": data.get("outstanding_amt"),
				"credit_amount_used": data.get("credit_limit") - data.get("credit_balance"),
				"months": dates,
				"payment_due_date":thirteenth_date_next_month,
				"opening_balance":first.get("balance")
	
			}
		return success_response(data=result)
	except Exception as e:
		frappe.logger('gl').exception(e)
		return error_response(e)


def get_dates(month):
	# month = "Dec 2022"
	m = month.split(" ")
	year = m[1]
	mth = m[0]
	from frappe.utils import getdate, get_first_day, get_last_day
	dt = getdate(f"{year}-{mth}-01")
	return get_first_day(dt), get_last_day(dt)


def export_ledger(kwargs):
	try:
		frappe.set_user("Administrator")
		from frappe.utils.xlsxutils import make_xlsx

		if kwargs.get("from_date") and kwargs.get("to_date"):
			start = getdate(kwargs.get("from_date"))
			end = getdate(kwargs.get("to_date"))
		else:
			start, end = get_dates(kwargs.get('month'))
		party = kwargs.get('party')
		if not party:
			party = frappe.db.get_value(
				"Customer", {"email", frappe.session.user})
		filters = {
			"company": kwargs.get('company', frappe.db.get_single_value("Global Defaults", "default_company")),
			"from_date": start, "to_date": end,
			"group_by": "Group by Voucher (Consolidated)", "include_dimensions": 1, "party_type": "Customer",
			"party": [party]
		}
		data = {}
		report = frappe.get_doc(
			"Report", "General Ledger", ignore_permissions=True)
		data["columns"], data["result"] = report.get_data(
			filters=filters, as_dict=True)

		columns = ["posting_date", "party", "balance",
				   "debit", "credit", "voucher_type", "voucher_no"]
		custom_idx = {"party": 1}
		xlsx_data, column_widths = build_xlsx_data(columns, data, custom_idx)

		xlsx_file = make_xlsx(xlsx_data, "Query Report",
							  column_widths=column_widths)

		frappe.response["filename"] = "report.xlsx"
		frappe.response["filecontent"] = xlsx_file.getvalue()
		frappe.response["type"] = "binary"
	except Exception as e:
		frappe.logger('gl').exception(e)
		return e


def build_xlsx_data(selected_column, data, cidx={}, include_indentation=False):
	import datetime
	from frappe.utils import cint, cstr

	EXCEL_TYPES = (
		str,
		bool,
		type(None),
		int,
		float,
		datetime.datetime,
		datetime.date,
		datetime.time,
		datetime.timedelta,
	)

	result = [[]]
	column_widths = []

	for column in data.get("columns"):
		if column.get("hidden") or column.get("fieldname") not in selected_column:
			continue
		column_width = cint(column.get("width", 0))
		# to convert into scale accepted by openpyxl
		column_width /= 10
		if idx := cidx.get(column.get("fieldname")):
			column_widths.insert(idx, column_width)
			result[0].insert(idx, _(column.get("label")))
		else:
			result[0].append(_(column.get("label")))
			column_widths.append(column_width)

	# build table from result
	for row_idx, row in enumerate(data.get("result")):
		row_data = []
		if isinstance(row, dict):
			for col_idx, column in enumerate(data.get("columns")):
				if column.get("hidden") or column.get("fieldname") not in selected_column:
					continue
				label = column.get("label")
				fieldname = column.get("fieldname")
				cell_value = row.get(fieldname, row.get(label, ""))
				if not isinstance(cell_value, EXCEL_TYPES):
					cell_value = cstr(cell_value)

				if cint(include_indentation) and "indent" in row and col_idx == 0:
					cell_value = (
						"	" * cint(row["indent"])) + cstr(cell_value)
				if idx := cidx.get(column.get("fieldname")):
					row_data.insert(idx, cell_value)
				else:
					row_data.append(cell_value)
		elif row:
			row_data = row

		result.append(row_data)

	result[1][1] = "Opening"
	result[-2][1] = "Total"
	result[-1][1] = "Closing (Opening + Total)"
	return result, column_widths
