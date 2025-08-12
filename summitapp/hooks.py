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
		"before_validate": "summitapp.customizations.address.events.before_validate"
	},
    "Contact": {
		"validate": "summitapp.customizations.contact.events.validate"
	},
	"Currency Exchange":{
		"validate":"summitapp.customizations.currency_exchange.events.validate"
	},
    "Customer Group":{
		"validate": "summitapp.customizations.customer_group.events.validate"
	},
	"Item":{
		"before_save": "summitapp.summitapp.customizations.item.events.on_save",
		"validate": "summitapp.summitapp.customizations.item.events.validate"
	},
	"Quotation": {
		"on_payment_authorized": "summitapp.summitapp.customizations.quotation.utils.on_payment_authorized",
		"validate": "summitapp.summitapp.customizations.quotation.events.validate"
	},
	"Customer":{
		"on_update": "summitapp.summitapp.customizations.customer.events.on_update",
		"before_save": "summitapp.summitapp.customizations.customer.events.on_save",
		"validate": "summitapp.summitapp.customizations.customer.events.validate"
	},
	"Sales Invoice":{
		"on_cancel":"summitapp.summitapp.customizations.sales_invoice.events.on_cancel",
		"on_submit": "summitapp.summitapp.customizations.sales_invoice.events.on_submit"
	},
	"Sales Order": {
		"on_payment_authorized": "summitapp.summitapp.customizations.sales_order.utils.on_payment_authorized",
		"on_submit": "summitapp.summitapp.customizations.sales_order.events.on_submit",
        "on_cancel": "summitapp.summitapp.customizations.sales_order.events.on_cancel",
        "validate": "summitapp.summitapp.customizations.sales_order.events.validate" ,
        "on_update_after_submit": "summitapp.summitapp.customizations.sales_order.events.on_update_after_submit",
        "autoname":"summitapp.summitapp.customizations.sales_order.events.autoname"
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

export_custom_fields = {"dt": ["in", ["Blog Post", "Brand", "Customer","Customer Group", 
                                      "Item", "Item Attribute Value", "Item Group", "Item Price", "Item Variant Attribute",
                                      "Quotation", "Quotation Item", "Tag"
                                      "Sales Invoice","Sales Order", "Sales Order Item", 
                                      ]], "module": ["=", "SummitApp"]}


after_migrate = "arcapp.migrate.after_migrate"
