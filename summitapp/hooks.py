from . import __version__ as app_version

app_name = "summitapp"
app_title = "SummitApp"
app_publisher = "8848 Digital LLP"
app_description = "Customizated APIs for Ecommerce"
app_email = "support@8848digital.com"
app_license = "MIT"


# include js in doctype views
doctype_js = {"Sales Order" : "public/js/sales_order.js",
              "Item" : "public/js/item.js"}

doc_events = {
	"Quotation": {
		"on_payment_authorized": "summitapp.overrides.quotation.on_payment_authorized",
		"validate": "summitapp.overrides.quotation.validate"
	},
	"Item":{
		"before_save": "summitapp.overrides.item.on_save",
		"validate": "summitapp.overrides.item.validate"
	},
	"Customer":{
		"on_update": "summitapp.overrides.customer.on_update",
		"before_save": "summitapp.overrides.customer.on_save",
		"validate": "summitapp.overrides.customer.validate"
	},
    "Contact": {
		"validate": "summitapp.overrides.contact.validate"
	},
	"Customer Group":{
		"validate": "summitapp.overrides.customer_group.validate"
	},
	"Sales Invoice":{
		"on_cancel":"summitapp.overrides.sales_invoice.on_cancel",
		"on_submit": "summitapp.overrides.sales_invoice.on_submit"
	},
	"Sales Order": {
		"on_payment_authorized": "summitapp.overrides.sales_order.on_payment_authorized",
		"on_submit": "summitapp.overrides.sales_order.on_submit",
        "on_cancel": "summitapp.overrides.sales_order.on_cancel",
        "validate": "summitapp.overrides.sales_order.validate" ,
        "on_update_after_submit": "summitapp.overrides.sales_order.on_update_after_submit",
        "autoname":"summitapp.overrides.sales_order.autoname"
	},
	"*": {
		"validate": "summitapp.utils.autofill_slug"
	},
	"Address": {
		"before_validate": "summitapp.overrides.address.before_validate"
	},
	"Currency Exchange":{
		"validate":"summitapp.overrides.currency_exchange.validate"
	}
}


override_whitelisted_methods = {
	"erpnext.controllers.item_variant.get_variant": "summitapp.overrides.item_variant.get_variant",
}


# User Data Protection
# --------------------

user_data_fields = [
	{
		"doctype": "{doctype_1}",
		"filter_by": "{filter_by}",
		"redact_fields": ["{field_1}", "{field_2}"],
		"partial": 1,
	},
	{
		"doctype": "{doctype_2}",
		"filter_by": "{filter_by}",
		"partial": 1,
	},
	{
		"doctype": "{doctype_3}",
		"strict": False,
	},
	{
		"doctype": "{doctype_4}"
	}
]

jinja = {
    "methods": [
		"summitapp.api.v1.product.check_availability"
	]
}

scheduler_events = {
	"cron": {
		"0 0 * * *":[
			"summitapp.overrides.currency_exchange.create_currency_exchange_records"
		],
  		"*/5 * * * *": [
			"summitapp.summitapp.scheduler.resize_image.resize_image",
        ]
	},
 }

# import summitapp.monkey_patches
# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"summitapp.auth.validate"
# ]

fixtures = [
    {"dt": "Custom Field", "filters": [
        [
            "module", "=", "SummitApp"
        ]
    ]},
    {"dt": "Property Setter", "filters": [
        [
            "module", "=", "SummitApp"
        ]
    ]},
    {"dt": "Workspace", "filters": [
        [
            "module", "=", "SummitApp"
        ]
    ]},
    {"dt": "Role", "filters": [
        [
            "name",
            "in",
            ["System Admin","Merchandiser","Operations Head"],
        ]
    ]},
    {"dt": "Custom DocPerm", "filters": [
        [
            "role",
            "in",
            ["System Admin","Merchandiser","Operations Head","Guest"],
        ]
    ]},
    {"dt": "Workflow", "filters": [
        [
            "name",
            "in",
            ["Sales Order Status"],
        ]
    ]},
    {"dt": "Workflow State", "filters": [
        [
            "name",
            "in",
            ["Cancelled"],
        ]
    ]},
    {"dt": "Workflow Action Master", "filters": [
        [
            "name",
            "in",
            ["Cancel"],
        ]
    ]}
]

# after_migrate = "summitapp.transalations.create_translations"
after_migrate = "summitapp.migrate.after_migrate"

before_migrate = "summitapp.utils.create_fields_in_user_doctype"

auth_hooks = [
	"summitapp.utils.validate_user_activity"
]