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
    "Address": {
		"before_validate": "summitapp.customizations.address.address.before_validate"
	},
    "Contact": {
		"validate": "summitapp.customizations.contact.contact.validate"
	},
	"Currency Exchange":{
		"validate":"summitapp.customizations.currency_exchange.currency_exchange.validate"
	},
    "Customer Group":{
		"validate": "summitapp.customizations.customer_group.customer_group.validate"
	},
	"Item":{
		"before_save": "summitapp.summitapp.customizations.item.item.on_save",
		"validate": "summitapp.summitapp.customizations.item.item.validate"
	},
	"Quotation": {
		"on_payment_authorized": "summitapp.summitapp.customizations.quotation.utils.on_payment_authorized",
		"validate": "summitapp.summitapp.customizations.quotation.quotation.validate"
	},
	"Customer":{
		"on_update": "summitapp.summitapp.customizations.customer.customer.on_update",
		"before_save": "summitapp.summitapp.customizations.customer.customer.on_save",
		"validate": "summitapp.summitapp.customizations.customer.customer.validate"
	},
	"Sales Invoice":{
		"on_cancel":"summitapp.summitapp.customizations.sales_invoice.sales_invoice.on_cancel",
		"on_submit": "summitapp.summitapp.customizations.sales_invoice.sales_invoice.on_submit"
	},
	"Sales Order": {
		"on_payment_authorized": "summitapp.summitapp.customizations.sales_order.utils.on_payment_authorized",
		"on_submit": "summitapp.summitapp.customizations.sales_order.sales_order.on_submit",
        "on_cancel": "summitapp.summitapp.customizations.sales_order.sales_order.on_cancel",
        "validate": "summitapp.summitapp.customizations.sales_order.sales_order.validate" ,
        "on_update_after_submit": "summitapp.summitapp.customizations.sales_order.sales_order.on_update_after_submit",
        "autoname":"summitapp.summitapp.customizations.sales_order.sales_order.autoname"
	},
	"*": {
		"validate": "summitapp.utils.autofill_slug"
	}
}


override_whitelisted_methods = {
	"erpnext.controllers.item_variant.get_variant": "summitapp.summitapp.customizations.item_variant.utils.get_variant",
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
			"summitapp.summitappp.customizations.currency_exchange.utils.create_currency_exchange_records"
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
