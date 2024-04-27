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
    role = Column(String, index=True, default="user")
    company_id = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    traits = relationship('Traits', back_populates='users')
    chosen_traits = relationship('ChosenTraits', back_populates='users')

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

    users = relationship('Users', backref='forms', foreign_keys=[user_id])
    questions = relationship('Questions', back_populates='forms')
    answers = relationship('Answers', back_populates='forms') 
    sprints = relationship('Sprints', back_populates='forms')
    chosen_traits = relationship('ChosenTraits', back_populates='forms')

class ChosenTraits(Base):
    __tablename__ = 'chosen_traits'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    name = Column(String, index=True)
    trait_id = Column(UUID(as_uuid=True), ForeignKey("traits.id"))
    trait_type = Column(String, index=True)
    form_id = Column(UUID(as_uuid=True), ForeignKey("forms.id"))
    practice_id = Column(UUID(as_uuid=True), ForeignKey("practices.id"))
    t_score = Column(Integer, index=True)

    users = relationship('Users', back_populates='chosen_traits')
    traits = relationship('Traits', back_populates='chosen_traits')
    practices = relationship('Practices', back_populates='chosen_traits')
    forms = relationship('Forms', back_populates='chosen_traits')

class Questions(Base):
    __tablename__ = 'questions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, index=True)
    category = Column(String, index=True)
    form_id = Column(UUID(as_uuid=True), ForeignKey("forms.id"))
    option_type = Column(String, index=True)
    rank = Column(Integer, index=True, default=0)

    forms = relationship('Forms', back_populates='questions') 
    options = relationship('Options', back_populates='questions')
    answers = relationship('Answers', back_populates='questions')

class Traits(Base):
    __tablename__ = 'traits'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    name = Column(String, index=True)
    average = Column(Float, index=True)
    standard_deviation = Column(Float, index=True)
    total_raw_score = Column(Integer, index=True)
    t_score = Column(Integer, index=True)

    users = relationship('Users', back_populates='traits')
    chosen_traits = relationship('ChosenTraits', back_populates='traits')

class Options(Base):
    __tablename__ = 'options'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, index=True)
    type = Column(String, index=True)
    trait_name = Column(String, index=True)
    question_id = Column(UUID(as_uuid=True), ForeignKey('questions.id'))

    questions = relationship('Questions', back_populates='options')
    answers = relationship('Answers', back_populates='options')

class Answers(Base):
    __tablename__ = 'answers'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    form_id = Column(UUID(as_uuid=True), ForeignKey('forms.id'))
    question_id = Column(UUID(as_uuid=True), ForeignKey('questions.id'))
    option_id = Column(UUID(as_uuid=True), ForeignKey('options.id'))
    answer = Column(String, index=True)

    forms = relationship('Forms', back_populates='answers')
    questions = relationship('Questions', back_populates='answers')
    options = relationship('Options', back_populates='answers')

class Practices(Base):
    __tablename__ = 'practices'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, index=True)
    score = Column(Integer, index=True)

    chosen_traits = relationship('ChosenTraits', back_populates='practices')


Base.metadata.create_all(engine)