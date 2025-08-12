from summitapp.summitapp.customizations.quotation.utils import custom_calculate_taxes_and_totals

def validate(self, method=None):
	custom_calculate_taxes_and_totals(self, method)
	