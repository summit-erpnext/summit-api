import frappe
from summitapp.summitapp.customizations.user.signin import (user_signin, allow_existing_user_signin, user_profile, 
                                                            guest_user_signin, redirecting_urls)

# User Signin
@frappe.whitelist()
def signin(kwargs):
	return user_signin(kwargs)


# Existing User Signin
@frappe.whitelist()
def existing_user_signin(kwargs):
    return allow_existing_user_signin(kwargs)


# Get User Profile
@frappe.whitelist()
def get_user_profile(kwargs):
	return user_profile(kwargs)


# Guest Iser Signin
@frappe.whitelist()    
def signin_as_guest(kwargs):
	return guest_user_signin(kwargs)


# Get Redirecting URLS
@frappe.whitelist()
def get_redirecting_urls(kwargs):
	return redirecting_urls(kwargs)