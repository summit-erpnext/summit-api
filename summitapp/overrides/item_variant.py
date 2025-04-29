import frappe
import json
from frappe import _
from erpnext.controllers.item_variant import (
    find_variant,
    make_variant_based_on_manufacturer,
)


@frappe.whitelist()
def get_variant(
    template, args=None, variant=None, manufacturer=None, manufacturer_part_no=None
):
    """Validates Attributes and their Values, then looks for an exactly
    matching Item Variant

    :param item: Template Item
    :param args: A dictionary with "Attribute" as key and "Attribute Value" as value
    """
    if args:
        if isinstance(args, str):
            args = json.loads(args)
        for attribute_name, attribute_value in args.items():
            if frappe.db.get_value(
                "Item Attribute", attribute_name, "numeric_values"
            ) != 1 and not frappe.db.exists(
                "Item Attribute Value",
                {"parent": attribute_name, "attribute_value": attribute_value},
            ):
                frappe.throw(
                    _(
                        f"For attribute '{attribute_name}', attribute value '{attribute_value}' does not exist. Please add it in the '<a href='/app/item-attribute/{attribute_name}' target='_blank'>Item Attribute'</a> Value table."
                    )
                )

    item_template = frappe.get_doc("Item", template)

    if item_template.variant_based_on == "Manufacturer" and manufacturer:
        return make_variant_based_on_manufacturer(
            item_template, manufacturer, manufacturer_part_no
        )
    else:
        if isinstance(args, str):
            args = json.loads(args)

        if not args:
            frappe.throw(
                _("Please specify at least one attribute in the Attributes table")
            )
        return find_variant(template, args, variant)
