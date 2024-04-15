import uuid
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime 
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database.connection import Base, engine
from sqlalchemy.orm import relationship

class Users(Base):
    __tablename__ = 'users'

    id = Column(String, primary_key=True, index=True)
    email = Column(String, index=True)
    first_name = Column(String, index=True)
    last_name = Column(String, index=True)
    role = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    form_id = Column(UUID(as_uuid=True), ForeignKey("forms.id")) 

    

class DevelopmentPlan(Base):
    __tablename__ = 'development_plan'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, index=True)

class UserDevelopmentPlan(Base):
    __tablename__ = 'user_development_plan'

    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    development_plan_id = Column(UUID(as_uuid=True), ForeignKey("development_plan.id"), primary_key=True)

class Forms(Base):
    __tablename__ = 'forms'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, index=True)
    user_id = Column(String, ForeignKey("users.id"))

    questions = relationship('Questions', back_populates='forms') 

class UserTraits(Base):
    __tablename__ = 'user_traits'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    traits_id = Column(UUID(as_uuid=True), ForeignKey("traits.id"))
    score = Column(Integer, index=True)

class Questions(Base):
    __tablename__ = 'questions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, index=True)
    forms_id = Column(UUID(as_uuid=True), ForeignKey("forms.id"))
    option_type = Column(String, index=True)

    forms = relationship('Forms') 
    options = relationship('Options', back_populates='questions')
    answers = relationship('Answers', back_populates='questions')

class Traits(Base):
    __tablename__ = 'traits'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, index=True)
    option_id = Column(UUID(as_uuid=True), ForeignKey('options.id'))

class Options(Base):
    __tablename__ = 'options'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, index=True)
    type = Column(String, index=True)
    question_id = Column(UUID(as_uuid=True), ForeignKey('questions.id'))
    
    questions = relationship('Questions') 

class Categories(Base):
    __tablename__ = 'categories'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, index=True)
    score = Column(Integer, index=True)
    trait_id = Column(UUID(as_uuid=True), ForeignKey('traits.id'))

class Answers(Base):
    __tablename__ = 'answers'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(String, ForeignKey('users.id'))
    question_id = Column(UUID(as_uuid=True), ForeignKey('questions.id'))
    option_id = Column(UUID(as_uuid=True), ForeignKey('options.id'))
    answer = Column(String, index=True)
    
    questions = relationship('Questions') 


Base.metadata.create_all(engine)
