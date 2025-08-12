from summitapp.summitapp.customizations.currency_exchange.utils import create_currency_exchange_records

def validate(self, method=None):
        create_currency_exchange_records(self)
