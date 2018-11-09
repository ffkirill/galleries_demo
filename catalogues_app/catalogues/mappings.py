from sqlalchemy import Column, String
from sqlalchemy_utils import UUIDType
from sa_helper import BaseMapping

class Country(BaseMapping):
    __tablename__ = 'country'

    id = Column(UUIDType, primary_key=True)
    name = Column(String(length=200))
    description = Column(String(length=400))

class EyeColor(BaseMapping):
    __tablename__ = 'eye_color'

    id = Column(UUIDType, primary_key=True)
    name = Column(String(length=200))
    description = Column(String(length=400))
