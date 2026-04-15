from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class LogEntry(Base):
    __tablename__ = "log_entries"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, index=True)
    domain = Column(String, index=True)
    email = Column(String, index=True)

class DomainList(Base):
    __tablename__ = "domain_lists"
    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String, unique=True, index=True)
    list_type = Column(String, index=True)  # 'direct' or 'proxy'
