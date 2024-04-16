import uuid
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Float 
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

    forms = relationship('Forms', back_populates='users')
    user_traits = relationship('UserTraits', back_populates='users')

class Sprints(Base):
    __tablename__ = 'sprints'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(Integer, index=True)

    forms = relationship('Forms', back_populates='sprints')

class DevelopmentPlan(Base):
    __tablename__ = 'development_plan'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, index=True)

class UserDevelopmentPlan(Base):
    __tablename__ = 'user_development_plan'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    development_plan_id = Column(UUID(as_uuid=True), ForeignKey("development_plan.id"))

class Forms(Base):
    __tablename__ = 'forms'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    sprint_id = Column(UUID(as_uuid=True), ForeignKey("sprints.id"))

    users = relationship('Users', back_populates='forms')
    questions = relationship('Questions', back_populates='forms') 
    sprints = relationship('Sprints', back_populates='forms')
    user_traits = relationship('UserTraits', back_populates='forms')

class UserTraits(Base):
    __tablename__ = 'user_traits'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    trait_id = Column(UUID(as_uuid=True), ForeignKey("traits.id"))
    form_id = Column(UUID(as_uuid=True), ForeignKey("forms.id"))
    practice_id = Column(UUID(as_uuid=True), ForeignKey("practices.id"))
    t_score = Column(Integer, index=True)

    users = relationship('Users', back_populates='user_traits')
    traits = relationship('Traits', back_populates='user_traits')
    practices = relationship('Practices', back_populates='user_traits')
    forms = relationship('Forms', back_populates='user_traits')

class Questions(Base):
    __tablename__ = 'questions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, index=True)
    forms_id = Column(UUID(as_uuid=True), ForeignKey("forms.id"))
    option_type = Column(String, index=True)

    forms = relationship('Forms', back_populates='questions') 
    options = relationship('Options', back_populates='questions')
    answers = relationship('Answers', back_populates='questions')

class Traits(Base):
    __tablename__ = 'traits'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, index=True)
    average = Column(Float, index=True)
    standard_deviation = Column(Float, index=True)
    total_raw_score = Column(Integer, index=True)
    t_score = Column(Integer, index=True)
    option_id = Column(UUID(as_uuid=True), ForeignKey('options.id'))

    options = relationship('Options', back_populates='traits')
    user_traits = relationship('UserTraits', back_populates='traits')

class Options(Base):
    __tablename__ = 'options'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, index=True)
    type = Column(String, index=True)
    raw_score = Column(Integer, index=True)
    question_id = Column(UUID(as_uuid=True), ForeignKey('questions.id'))
    traits_id = Column(UUID(as_uuid=True), ForeignKey('traits.id'))

    questions = relationship('Questions', back_populates='options') 
    traits = relationship('Traits', back_populates='options')
    answers = relationship('Answers', back_populates='options')

class Answers(Base):
    __tablename__ = 'answers'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(String, ForeignKey('users.id'))
    question_id = Column(UUID(as_uuid=True), ForeignKey('questions.id'))
    option_id = Column(UUID(as_uuid=True), ForeignKey('options.id'))
    answer = Column(String, index=True)

    questions = relationship('Questions', back_populates='answers')
    options = relationship('Options', back_populates='answers')

class Practices(Base):
    __tablename__ = 'practices'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, index=True)
    score = Column(Integer, index=True)

    user_traits = relationship('UserTraits', back_populates='practices')


Base.metadata.create_all(engine)
