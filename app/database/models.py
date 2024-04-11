import uuid
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from app.database.connection import Base, engine

class Traits(Base):
    __tablename__ = 'traits'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String)
    option_id = Column(UUID(as_uuid=True), ForeignKey('options.id'))

class Options(Base):
    __tablename__ = 'options'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String)
    type = Column(String)
    question_id = Column(UUID(as_uuid=True), ForeignKey('questions.id'))

class Categories(Base):
    __tablename__ = 'categories'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String)
    score = Column(Integer)
    trait_id = Column(UUID(as_uuid=True), ForeignKey('traits.id'))

class Answers(Base):
    __tablename__ = 'answers'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(String, ForeignKey('users.id'))
    question_id = Column(UUID(as_uuid=True), ForeignKey('questions.id'))
    option_id = Column(UUID(as_uuid=True), ForeignKey('options.id'))
    answer = Column(String)

Base.metadata.create_all(engine)
