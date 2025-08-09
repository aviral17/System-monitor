from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session, relationship

Base = declarative_base()

class Machine(Base):
    __tablename__ = 'machines'
    id = Column(Integer, primary_key=True)
    uuid = Column(String(64), unique=True)
    hostname = Column(String(256))
    os_platform = Column(String(128))
    os_version = Column(String(256))
    username = Column(String(128))
    cpu_cores = Column(Integer)
    memory_mb = Column(Integer)
    last_seen = Column(Integer)
    reports = relationship('Report', backref='machine')

class Report(Base):
    __tablename__ = 'reports'
    id = Column(Integer, primary_key=True)
    machine_id = Column(Integer, ForeignKey('machines.id'))
    timestamp = Column(Integer)
    disk_encryption = Column(Boolean)
    os_updates = Column(Boolean)
    antivirus = Column(Boolean)
    sleep_settings = Column(Boolean)
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    disk_usage = Column(Float)
    raw = Column(String)
    disk_info = Column(String)

engine = create_engine('sqlite:///monitor.db')
Session = sessionmaker(bind=engine)
db_session = scoped_session(Session)

def init_db():
    Base.metadata.create_all(engine)