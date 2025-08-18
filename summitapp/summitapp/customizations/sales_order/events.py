from summitapp.summitapp.customizations.sales_order.utils import (on_submit_actions, on_cancel_set_order_status, send_sales_order_api,
                                                                set_workflow_state_and_order_status, on_update_after_submit_set_workflow_state,
                                                                set_autoname)

def on_submit(self, method=None):
    on_submit_actions(self)


def on_cancel(self, method=None):
    on_cancel_set_order_status(self)


def validate(self, method=None):
    send_sales_order_api(self)
    set_workflow_state_and_order_status(self)


def on_update_after_submit(self, method=None):
    on_update_after_submit_set_workflow_state(self)


def autoname(self,method=None):
    set_autoname(self)
