import uuid

from sqlalchemy import Column, Integer, String, JSON, ForeignKey, Boolean, DateTime, Date, NUMERIC, Table, Text
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
from sqlalchemy.orm import validates

Base = declarative_base()


class Fkinds(Base):
    __tablename__ = 'fkinds'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(32), unique=True)
    description = Column(String(191))
    created_at = Column(Integer)
    skinds = relationship("Skinds", back_populates="fkinds", cascade="all, delete-orphan")


class Skinds(Base):
    __tablename__ = 'skinds'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(32))
    parent_id = Column(Integer, ForeignKey('fkinds.id'))
    description = Column(String(191))
    created_at = Column(Integer)
    fkinds = relationship("Fkinds", back_populates="skinds")
    tkinds = relationship("Tkinds", back_populates="skinds", cascade="all, delete-orphan")


# Association table for User and Tkinds
user_tkinds_association = Table(
    'user_tkinds_association',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('tkinds_id', Integer, ForeignKey('tkinds.id'), primary_key=True)
)


class Tkinds(Base):
    __tablename__ = 'tkinds'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(32))
    parent_id = Column(Integer, ForeignKey('skinds.id'))
    data_level = Column(String(32))
    regex = Column(String(128))
    sen_word = Column(JSON)
    if_sen = Column(Integer)
    description = Column(String(191))
    created_at = Column(Integer)
    # Relationships
    skinds = relationship("Skinds", back_populates="tkinds")
    users = relationship("User", secondary=user_tkinds_association, back_populates="tkinds")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)  # Username length up to 50 characters
    password = Column(String(255))  # Password length up to 255 characters (hashed passwords are long)
    email = Column(String(120), unique=True, index=True)  # Email length up to 120 characters
    status = Column(String(20))  # Status length up to 20 characters
    display_name = Column(String(100))  # Display name length up to 100 characters
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Relationships
    tkinds = relationship("Tkinds", secondary=user_tkinds_association, back_populates="users")

    @validates('email')
    def validate_email(self, key, address):
        if '@' not in address:
            raise ValueError("提供的邮箱地址无效")
        return address


class ModelCost(Base):
    __tablename__ = 'model_cost'
    id = Column(Integer, primary_key=True, index=True)
    manufacturer = Column(String(32), default="")
    model_name = Column(String(32), default="")
    input_price = Column(String(32), default="")
    output_price = Column(String(32), default="")
    train_price = Column(String(32), default="")
    date = Column(Date)
    unit = Column(String(32), default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class GptUserContent(Base):
    __tablename__ = "gpt_user_content"
    id = Column(Integer, primary_key=True, index=True)
    uid = Column(String(50), index=True, default=str(uuid.uuid4()))
    username = Column(String(50), index=True)
    content = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SensitiveWordRecord(Base):
    __tablename__ = "sensitive_word_record"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), index=True)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
