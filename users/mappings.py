from sqlalchemy import Column, String
from sqlalchemy_utils import UUIDType, EmailType, PasswordType, force_auto_coercion
from sa_helper import BaseMapping

force_auto_coercion()

class User(BaseMapping):
    __tablename__ = 'user'

    id = Column(UUIDType, primary_key=True)
    name = Column(String(length=200))
    last_name = Column(String(length=200))
    father_name = Column(String(length=200))
    password = Column(PasswordType(schemes=['pbkdf2_sha512'], max_length=50))
    email = Column(EmailType, index=True, unique=True)
    country_id = Column(UUIDType, nullable=True)
    eyes_id = Column(UUIDType, nullable=True)
