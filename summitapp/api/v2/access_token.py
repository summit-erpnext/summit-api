from summitapp.summitapp.customizations.user.utils import get_api_token, get_token_with_email, get_token_with_mobile

# Get Access token from user
def get_access_token(kwargs):
    return get_api_token(kwargs)


def get_token(email):
    return get_token_with_email(email)


def get_token_with_mobile(mobile):
    return get_token_with_mobile(mobile)


    
