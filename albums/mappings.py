from sqlalchemy import Column, String, ForeignKey
from sqlalchemy_utils import UUIDType, URLType, JSONType
from sa_helper import BaseMapping

class Album(BaseMapping):
    __tablename__ = 'album'

    id = Column(UUIDType, primary_key=True)
    user_id = Column(UUIDType, ForeignKey('user.id'), nullable=False)
    name = Column(String(length=200))
    description = Column(String(length=300), default='')

class Photo(BaseMapping):
    __tablename__ = 'photo'

    id = Column(UUIDType, primary_key=True)
    album_d = Column(UUIDType, ForeignKey('album.id'), nullable=False)
    orig_file = Column(URLType, default='', nullable=False)
    thumbnails = Column(JSONType)
