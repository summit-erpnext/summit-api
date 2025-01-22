import frappe
import requests

def validate(self, method=None):
        create_currency_exchange_records()

def create_currency_exchange_records():
    api_url = "https://api.exchangerate-api.com/v4/latest/INR"
    response = requests.get(api_url)

    if response.status_code == 200:
        data = response.json()
        base_currency = data['base']
        rates = data['rates']

        enabled_currencies = frappe.get_all("Currency", filters={"enabled": 1}, pluck="name")

        for to_currency, exchange_rate in rates.items():
            if to_currency == base_currency or to_currency not in enabled_currencies:
                continue

            existing_record = frappe.get_all(
                "Currency Exchange",
                filters={
                    "from_currency": base_currency,
                    "to_currency": to_currency,
                    "date": frappe.utils.nowdate(),
                },
                limit=1,
            )

            if not existing_record:
                currency_exchange = frappe.get_doc({
                    "doctype": "Currency Exchange",
                    "from_currency": base_currency,
                    "to_currency": to_currency,
                    "exchange_rate": exchange_rate,
                    "date": frappe.utils.nowdate(),
                    "for_buying": 1,
                    "for_selling": 1,
                })
                currency_exchange.flags.ignore_validate = True
                currency_exchange.insert()
                frappe.logger().info(
                    f"Created Currency Exchange record: {base_currency} to {to_currency} at rate {exchange_rate}"
                )
            else:
                frappe.logger().info(
                    f"Record already exists for {base_currency} to {to_currency} on {frappe.utils.nowdate()}"
                )
    else:
        frappe.logger().error(f"Failed to fetch exchange rates. API response: {response.text}")
