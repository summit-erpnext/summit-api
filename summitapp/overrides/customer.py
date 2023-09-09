import frappe
from summitapp.summitapp.doctype.web_settings.web_settings import add_category_from_sub
from frappe import _

def on_save(self, method):
	if self.email:
		self.email_id = self.email
	if self.mobile_number:
		self.mobile_no = self.mobile_number 
	
def validate(self, method=None):
	if self.get("first_name") or self.get("last_name"):
		self.full_name = f'{self.get("first_name")} {self.get("last_name")}'
		self.full_name = self.full_name.strip()
	add_category_from_sub(self, "select_sub_category", "select_category")

def on_update(self, method=None):
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