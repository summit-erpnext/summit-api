import frappe
from frappe.utils import random_string
from frappe.utils.password import get_decrypted_password

# sport_network.utils.check_user_exists




def success_response(data=None, id=None):
	response = {'msg': 'success'}
	response['data'] = data
	if id:
		response['data'] = {'id': id, "name": id}
	return response


def error_response(err_msg):
	return {
		'msg': 'error',
		'error': err_msg
	}



def send_mail(template_name, recipients, context):
	frappe.sendmail(
		recipients=recipients,
		subject=frappe.render_template(
			frappe.db.get_value(
				"Email Template", template_name, "subject"
			),
			context,
		),
		cc="",
		bcc="",
		delayed=False,
		message=frappe.render_template(
			frappe.db.get_value(
				"Email Template", template_name, "response"
			),
			context,
		),
		reference_doctype="",
		reference_name="",
		attachments="",
		print_letterhead=False,
	)
	return "Email Sent"


def create_temp_user(kwargs):
    try:
        frappe.local.login_manager.login_as("Administrator")
        username = random_string(8)
        usr = frappe.get_doc({
            "doctype": "User",
            "email": username + "@random.com",
            "first_name": "TGuest",
            "send_welcome_email": 0,
            "language": kwargs.get("language_code"),
        }).insert()
        usr.add_roles("Customer") 
        # frappe.local.login_manager.login_as(usr.email)
        return usr.email
    except Exception as e:
        frappe.logger('cart').exception(e)
        return error_response(e)



def create_access_token(kwargs):
    try:
        token = random_string(20)
        email = create_temp_user(kwargs)
        access = frappe.get_doc({
            "doctype": "Access Token",
            "token": token,
            "email": email
        }).insert()
        return access.token, access.email
    except Exception as e:
        frappe.logger('cart').exception(e)
        return error_response(e)



def update_customer(customer=None, data={}):
	if customer:
		doc = frappe.get_doc("Customer", customer)
		doc.update(data).save()
	else:
		doc = frappe.get_doc({
			"doctype": "Customer",
			"customer_group": "Customer",
			"customer_type": "Individual",
			"territory": "All Territories",
		}).update(data).insert(ignore_permissions=True)
	return doc.name


def get_company_address(company):
	from frappe.contacts.doctype.address.address import get_default_address
	ret = frappe._dict()
	ret.company_address = get_default_address("Company", company)
	ret.gstin = frappe.db.get_value("Address", ret.company_address, 'gstin')

	return ret


def sync_contact(old_id, new_id):
	frappe.local.login_manager.login_as("Administrator")
	if temp := frappe.db.exists("Contact", {"user": old_id}):
		frappe.delete_doc("Contact", temp)
	contact = frappe.get_doc("Contact", {"email_id": new_id})
	contact.user = new_id
	contact.save()


@frappe.whitelist()
def sync_guest_user(email):
	if "random" in frappe.session.user:
		temp = frappe.session.user
		frappe.rename_doc("User", frappe.session.user, email)
		sync_contact(temp, email)
		frappe.local.login_manager.login_as(email)
	else:
		return


def check_guest_user(email=frappe.session.user):
	return 'random' in email


@frappe.whitelist(allow_guest=True)
def download_pdf(
	doctype, name, format=None, doc=None, no_letterhead=0, language=None, letter_head=None
):
	from frappe.utils.print_format import download_pdf
	download_pdf(doctype, name, format=format,
				 doc=doc, no_letterhead=no_letterhead)


def autofill_slug(doc, method=None):
	if hasattr(doc, 'slug') and not doc.get('slug'):
		doc.slug = frappe.utils.slug(doc.name)


def get_access_level(customer_group=None):
	if customer_group:
		access_level = frappe.db.get_value(
			"Customer Group", customer_group, "access_level") or 0
		return access_level
	return 0







def make_payment_entry(sales_order):
	invoice = frappe.db.get_value(
		'Sales Invoice', {'sales_order': sales_order}, 'name')
	if invoice:
		dt = 'Sales Invoice'
		dn = invoice
	else:
		dt = 'Sales Order'
		dn = sales_order
	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
	from frappe.utils import getdate
	payment_entry_doc = get_payment_entry(dt, dn)
	payment_entry_doc.reference_no = sales_order
	payment_entry_doc.reference_date = getdate()
	payment_entry_doc.save(ignore_permissions=True)
	payment_entry_doc.submit()

