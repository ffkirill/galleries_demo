from importlib import import_module
from django.conf import settings
from rest_framework.authentication import BaseAuthentication

def get_django_session_store():
    return import_module(settings.SESSION_ENGINE).SessionStore

def create_session_key(user_id):
    store = get_django_session_store()
    s = store()
    s['user_id'] = user_id
    s.create()
    return s.session_key

class AuthUser:
    id = None
    is_authenticated = False

    def __init__(self, user_id=None):
        if user_id is not None:
            self.id = user_id
            self.is_authenticated = True
        super()

class SessionIdAuthentication(BaseAuthentication):
    """
    Query param based authentication.

    Clients should authenticate by passing the session_key param in URL
    """

    def authenticate(self, request):
        session_id = request.GET.get('session_key', '').lower()
        return self.authenticate_credentials(session_id)

    def authenticate_credentials(self, key):
        store = get_django_session_store()
        session = store(session_key=key)
        return AuthUser(session.get('user_id', None)), key
