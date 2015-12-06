from datetime import datetime
from project.src.model.base import Base
from project.src.model.exception import NotFound
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import Column, Integer, String, DateTime

class Visitor(Base):
    __tablename__ = "visitor"

    id = Column(Integer, primary_key=True)
    ip = Column(String)
    referer = Column(String)
    user_agent = Column(String)
    url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __init__(self, request):
        self.ip = str(request.remote_addr)
        self.referer = request.headers.get('Referer')
        self.browser = request.headers.get('User-Agent')
        self.url = request.url