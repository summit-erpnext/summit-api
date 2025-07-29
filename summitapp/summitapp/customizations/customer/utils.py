import frappe
from summitapp.summitapp.doctype.web_settings.utils import add_category_from_sub
from frappe import _

def set_email_id_and_mobile_no(self, method):
	if self.email:
		self.email_id = self.email
	if self.mobile_number:
		self.mobile_no = self.mobile_number 
	

def set_full_name_add_category(self, method=None):
	if self.get("first_name") or self.get("last_name"):
		self.full_name = f'{self.get("first_name")} {self.get("last_name")}'
		self.full_name = self.full_name.strip()
	add_category_from_sub(self, "select_sub_category", "select_category")


def on_update_create_shipping_address_and_user(self, method=None):
	if self.flags.is_new_doc and self.get("s_address_title"):
		self.shipping_add = create_shipping_address(self)
	if self.flags.is_new_doc and self.get("is_user") and self.get("email") and not self.get("user"):
		if existing:=frappe.db.exists("User", self.get("email")):
			user = existing
		else:
			user = create_user(self)
		self.db_set("user", user)


def create_user(self):
	user_doc = frappe.get_doc({
		"doctype": 'User',
		'email': self.email,
		'send_welcome_email': False,
		'new_password': "shanparts@123",
		"first_name": self.get("first_name") or self.get("customer_name"),
		"last_name": self.get("last_name"),
		"full_name": self.get("full_name"),
		'roles': [{"doctype": "Has Role", "role": "Customer"}],
		'enabled': 1,
		'module_profile': "Customer"
	})
	user_doc.insert(ignore_permissions=True)

	return user_doc.name

def _create_primary_contact(self):
	if not self.customer_primary_contact and not self.lead_name:
		if self.mobile_no or self.email_id:
			contact = _make_contact(self)
			self.db_set("customer_primary_contact", contact.name)
			self.db_set("mobile_no", self.mobile_no)
			self.db_set("email_id", self.email_id)

def create_shipping_address(self):
	from frappe.contacts.doctype.address.address import get_address_display

	if self.flags.is_new_doc and self.get("s_address_line1"):
		address = make_shipping_address(self)

def _create_primary_address(self):
	from frappe.contacts.doctype.address.address import get_address_display

	if self.flags.is_new_doc and self.get("address_line1"):
		address = _make_address(self)
		address_display = get_address_display(address.name)

		self.db_set("customer_primary_address", address.name)
		self.db_set("primary_address", address_display)

def _make_contact(args, is_primary_contact=1):
	contact = frappe.get_doc(
		{
			"doctype": "Contact",
			"first_name": args.get("first_name") or args.get("customer_name"),
			"is_primary_contact": is_primary_contact,
			"salutation": args.salutation,
			"last_name": args.get("last_name"),
			"full_name": args.get("full_name"),
			"email_id": args.get("email"),
			"phone": args.get("mobile_number"),
			"designation": args.get("contact_designation"),
			"links": [{"link_doctype": args.get("doctype"), "link_name": args.get("name")}],
		}
	)
	if args.get("email_id"):
		contact.add_email(args.get("email_id"), is_primary=True)
	if args.get("mobile_number"):
		contact.add_phone(args.get("mobile_number"), is_primary_mobile_no=True)
	contact.insert()

	return contact


def make_shipping_address(doc):
	address = frappe.get_doc(
        {
            "doctype": "Address",
            "address_type": "Shipping",
            "address_title": doc.get("s_address_title"),
            "address_line1": doc.get("s_address_line1"),
            "address_line2": doc.get("s_address_line2"),
            "city": doc.get("s_city"),
            "state": doc.get("s_state"),
            "pincode": doc.get("s_pincode"),
            "country": doc.get("s_country"),
			"is_shipping_address": 1,
			"gst_category": doc.get("gst_category") or "Unregistered",
			"links": [{"link_doctype": doc.get("doctype"), "link_name": doc.get("name")}],
        }
    ).insert(ignore_mandatory=True)
	
	return address


def _make_address(args, is_primary_address=1):
	reqd_fields = []
	for field in ["city", "country"]:
		if not args.get(field):
			reqd_fields.append("<li>" + field.title() + "</li>")

	if reqd_fields:
		msg = _("Following fields are mandatory to create address:")
		frappe.throw(
			"{0} <br><br> <ul>{1}</ul>".format(msg, "\n".join(reqd_fields)),
			title=_("Missing Values Required"),
		)

	address = frappe.get_doc(
		{
			"doctype": "Address",
			"address_type": "Billing",
			"address_title": args.get("address_title"),
			"address_line1": args.get("address_line1"),
			"address_line2": args.get("address_line2"),
			"city": args.get("city"),
			"state": args.get("state"),
			"pincode": args.get("pincode"),
			"country": args.get("country"),
			"is_primary_address": is_primary_address,
			"gst_category": args.get("gst_category") or "Unregistered",
			"links": [{"link_doctype": args.get("doctype"), "link_name": args.get("name")}],
		}
	).insert()

	return address



import frappe
import erpnext
from summitapp.utils import error_response, success_response
from summitapp.api.v2.customer_address import get_details as get_address_details


def get_user_profile(kwargs):
	try:
		email = frappe.session.user
		if not frappe.db.exists('Customer', {'email': email}):
			return error_response('Customer/Dealer Does Not Exist')
		cust_doc = frappe.get_doc('Customer', {'email': email})
		roles = frappe.get_roles(email)
		if 'Customer' in roles:
			return get_customer_profile(cust_doc)
		elif 'Dealer' in roles:
			return get_dealer_profile(cust_doc)
		else:
			return error_response('Logged In User Is Neither A Customer Nor A Dealer')
	except Exception as e:
		return error_response(e)


def get_customer_profile(cust_doc):
	try:
		cust_bill_address = None
		cust_ship_address = None
		coupon_codes = None
		if bill_add:=get_billing_address_doc(cust_doc, 'Billing'):
			cust_bill_address = get_address_details(cust_doc, bill_add)
		if ship_add:=get_billing_address_doc(cust_doc, 'Shipping', "is_shipping_address"):
			cust_ship_address = get_address_details(cust_doc, ship_add)
		allowed_coupons = []
		if cust_doc.get("assigned_coupon_code"):
			allowed_coupons = frappe.get_list("Available Coupons",{"parent":cust_doc.name},pluck='coupon_name', ignore_permissions=1)
			coupon_codes = frappe.get_list("Coupon Code", {"coupon_name": ["in", allowed_coupons]}, pluck='coupon_code', ignore_permissions=1)
		contact = frappe.db.get_value("Contact",{"email_id":cust_doc.email},["salutation","first_name", "middle_name", "last_name"], as_dict=1) or {}
		customer_name = None
		if contact:
			customer_name = [contact.get("first_name"),contact.get("middle_name"),contact.get("last_name")]
			customer_name = " ".join([part.strip() for part in customer_name if part])
		cust_details = {
			"profile_details":{
							"customer_id": cust_doc.name,
							"salutation": cust_doc.salutation or contact.get("salutation"),
							"customer_name": customer_name or cust_doc.customer_name,
							"first_name": contact.get("first_name"),
							"company_name": cust_doc.customer_name,
							"company_code": cust_doc.get("company_code"),
							"contact_no": cust_doc.mobile_number,
							"email": cust_doc.email,
							"payment_terms": cust_doc.payment_terms,
							"credit_limit": get_credit_limit(cust_doc)
							},
			"billing_address":  cust_bill_address or {},
			"shipping_address": cust_ship_address or {},
			"store_credit_details": {
					"balance": cust_doc.get("balance_amount"),
					"date": cust_doc.get("date")
			},
			"allowed_coupons": coupon_codes
		}
		return success_response(data=cust_details)

	except Exception as e:
		return error_response(e)

def get_credit_limit(cust_doc, company=None):
	if not company:
		company = (erpnext.get_default_company() or frappe.db.sql("""select name from tabCompany limit 1""")[0][0])
	credits = frappe.db.get_value("Customer Credit Limit", {"parent":cust_doc.name}, "credit_limit") or 0
	return credits

def get_dealer_profile(dealer_doc):
	try:
		if billing_add:=get_billing_address_doc(dealer_doc, 'Billing'):
			cust_bill_address = get_address_details(dealer_doc, billing_add)
		else:
			cust_bill_address = None

		if shipping_add:=get_billing_address_doc(dealer_doc, 'Shipping'):
			cust_ship_address = get_address_details(dealer_doc, shipping_add)
		else:
			cust_ship_address = None

		personal_details = get_billing_address_doc(dealer_doc, "Personal")
		if not personal_details:
			personal_details = cust_bill_address
		dealer_details = {
				"name": dealer_doc.name,
				"email": dealer_doc.email,
				"contact_no": dealer_doc.mobile_number,
				"seller_classification": dealer_doc.seller_classification,
				"total_credit_amount": get_store_credit(dealer_doc.name),
				"trading_company_name": dealer_doc.get('trading_company_name'),
				"billing_address": cust_bill_address.get('full_address') if cust_bill_address else '',
				"delivery_address": cust_ship_address.get('full_address') if cust_ship_address else '',
				"gst_number ": personal_details.get('gstin'),
				"country": personal_details.get('country'),
				"state": personal_details.get('state'),
				"city": personal_details.get('city'),
				"pin_code": personal_details.get('pincode'),
				"categories": [cat.name1 for cat in dealer_doc.select_category],
				"brands": [cat.name1 for cat in dealer_doc.select_brands_]
			}
		return success_response(data=dealer_details)
	except Exception as e:
		frappe.logger('utils').exception(e)
		return error_response(e)

def get_store_credit(user):
	try:
		user_list = frappe.db.get_list('Store Credit Assigned',{'user': user}, ['user as user_name'], group_by = 'user')
		for user in user_list:
			user['store_credit_assigned'] = sum(i.credit_amount for i in amount_list('Store Credit Assigned', user.user_name, 'credit_amount'))
			user['store_credit_used'] = sum(i.debit_amount for i in amount_list('Store Credit Used', user.user_name, 'debit_amount'))
			user['store_credit_balance'] = user['store_credit_assigned'] - user['store_credit_used']
		return user_list[0].get('store_credit_balance') if user_list else ''
	except Exception as e:
		return None

def amount_list(table, user, field):
	return frappe.db.get_list(table, {'user': user}, field)

def get_default_address(name, add_type, sort_key="is_primary_address"):
	"""Returns default Address name for the given doctype, name"""
	if sort_key not in ["is_shipping_address", "is_primary_address"]:
		return None

	out = frappe.db.sql(
		""" SELECT
			addr.name, addr.%s
		FROM
			`tabAddress` addr, `tabDynamic Link` dl
		WHERE
			dl.parent = addr.name and dl.link_doctype = 'Customer' and
			dl.link_name = %s and ifnull(addr.disabled, 0) = 0 and address_type = %s
		"""
		% (sort_key, "%s", "%s"),
		(name,add_type),
		as_dict=True,debug=1
	)

	if out:
		for contact in out:
			if contact.get(sort_key):
				return contact.name
		return out[0].name
	else:
		return None

def get_billing_address_doc(cust_doc, add_type, defaults="is_primary_address"):
	address = get_default_address(cust_doc.name, add_type, defaults)
	address_obj = {}
	if address:
		address_obj = frappe.get_doc("Address",address)
	return address_obj

def create_customer_inquiry(kwargs):
	doc = frappe.new_doc("Customer Inquiry")
	doc.email_id = frappe.session.user
	doc.search_text = kwargs.get("search_text")
	doc.item_part = kwargs.get("item_part")
	doc.model_of_item = kwargs.get("item_model")
	doc.description = kwargs.get("item_desc")
	doc.save(ignore_permissions=True)
	return success_response(data=doc.name)

def get_ageing_report(kwargs):
	if frappe.session.user == "Guest":
		return error_response("Please login first")
	customer = frappe.db.get_value('Customer', {'email': frappe.session.user})
	if not customer:
		return error_response("Customer not found")
	if not frappe.db.exists("DocType","Ageing Detail"):
		return success_response("Something went wrong!")
	report = frappe.get_list("Ageing Detail", {"customer_code":customer}, ["customer_code","customer_name","d_0_30","d_31_60","d_61_90","d_90_120","d_120_to_above"])
	return success_response(data=report)

def transporters(kwargs):
	if frappe.session.user == "Guest":
		return error_response("Please login first")
	transporters = frappe.get_all("Transporter", pluck='name1')
	return success_response(data=transporters)