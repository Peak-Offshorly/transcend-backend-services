import uuid
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from app.database.connection import Base, engine

class Traits(Base):
    __tablename__ = 'traits'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    trait = Column(String, index=True)
    score = Column(Integer, index=True)

class TraitsQuestions(Base):
    __tablename__ = 'traits_questions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    question = Column(String, index=True)
    trait_id = Column(UUID(as_uuid=True), ForeignKey("traits.id"))

class Accounts(Base):
    __tablename__ = 'users'

    id = Column(String, primary_key=True, index=True)
    email = Column(String, index=True)
    password = Column(String, index=True)
    first_name = Column(String, index=True)
    last_name = Column(String, index=True)

Base.metadata.create_all(engine)
