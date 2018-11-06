"""
Implements thread-local SA session reuse
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

def get_engine():
    """
    For lazy settings.SA_URL evaluation when Session()'s requested
    """
    from django.conf import settings
    return create_engine(settings.SA_DATABASE_URL)

def session_factory():
    engine = get_engine()
    fac = sessionmaker(bind=engine)
    return fac()

Session = scoped_session(session_factory)
BaseMapping = declarative_base()

__all__ = ['Session', 'BaseMapping', 'get_engine']
